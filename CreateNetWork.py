from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint, 
    QgsSpatialIndex, QgsProject, QgsFeatureRequest,
    QgsDistanceArea, QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant
import networkx as nx
from collections import defaultdict, deque
import math

class LineTopologyAnalyzer:
    """线图层拓扑关系分析器"""
    
    def __init__(self, line_layer, tolerance=0.001):
        """
        初始化分析器
        
        参数:
        line_layer: QgsVectorLayer - 线图层
        tolerance: float - 容差值，用于判断点是否相等
        """
        self.layer = line_layer
        self.tolerance = tolerance
        self.spatial_index = QgsSpatialIndex(self.layer.getFeatures())
        
        # 拓扑关系存储
        self.endpoint_connections = defaultdict(dict)  # 端点连接关系
        self.line_connections = defaultdict(lambda: defaultdict(list))  # 线段连接关系
        self.intersections = defaultdict(set)         # 相交关系
        self.adjacent_lines = defaultdict(set)        # 相邻关系
        
    def analyze_endpoint_connections(self):
        """分析端点连接关系"""
        features = list(self.layer.getFeatures())
        
        # 提取所有端点
        endpoints = {}  # 点坐标 -> 要素ID列表
        
        for feature in features:
            geom = feature.geometry()
            fid = feature.id()
            
            if geom.isMultipart():
                # 多部件几何
                lines = geom.asMultiPolyline()
                for line in lines:
                    if len(line) >= 2:
                        start_point = line[0]
                        end_point = line[-1]
                        
                        start_key = self._point_key(start_point)
                        end_key = self._point_key(end_point)
                        
                        endpoints.setdefault(start_key, list()).append({"fid":fid,"type":"s"})
                        endpoints.setdefault(end_key, list()).append({"fid":fid,"type":"e"})
            else:
                # 单部件几何
                line = geom.asPolyline()
                if len(line) >= 2:
                    start_point = line[0]
                    end_point = line[-1]
                    
                    start_key = self._point_key(start_point)
                    end_key = self._point_key(end_point)
                    
                    endpoints.setdefault(start_key, list()).append({"fid":fid,"type":"s"})
                    endpoints.setdefault(end_key, list()).append({"fid":fid,"type":"e"})
        # 建立端点连接关系
        for point_key, fids in endpoints.items():
            if len(fids) > 1:
                fid_list = list(fids)
                for i in range(len(fid_list)):
                    for j in range(i+1, len(fid_list)):
                        # self.endpoint_connections[fid_list[i]["fid"]][fid_list[i]["type"]]=nodekeyIndex
                        self.line_connections[fid_list[i]["fid"]][fid_list[i]["type"]].append(fid_list[j]["fid"])
                        self.line_connections[fid_list[j]["fid"]][fid_list[j]["type"]].append(fid_list[i]["fid"])
        
        return self.line_connections
    def analyze_endpoint_connections_virturalnode(self):
        """分析端点连接关系"""
        features = list(self.layer.getFeatures())
        
        # 提取所有端点
        endpoints = {}  # 点坐标 -> 要素ID列表
        
        for feature in features:
            geom = feature.geometry()
            fid = feature.id()
            
            if geom.isMultipart():
                # 多部件几何
                lines = geom.asMultiPolyline()
                for line in lines:
                    if len(line) >= 2:
                        start_point = line[0]
                        end_point = line[-1]
                        
                        start_key = self._point_key(start_point)
                        end_key = self._point_key(end_point)
                        
                        endpoints.setdefault(start_key, list()).append({"fid":fid,"type":"s"})
                        endpoints.setdefault(end_key, list()).append({"fid":fid,"type":"e"})
            else:
                # 单部件几何
                line = geom.asPolyline()
                if len(line) >= 2:
                    start_point = line[0]
                    end_point = line[-1]
                    
                    start_key = self._point_key(start_point)
                    end_key = self._point_key(end_point)
                    
                    endpoints.setdefault(start_key, list()).append({"fid":fid,"type":"s"})
                    endpoints.setdefault(end_key, list()).append({"fid":fid,"type":"e"})
        # 建立端点连接关系
        nodekeyIndex = 0
        for point_key, fids in endpoints.items():
            if len(fids) > 0:
                fid_list = list(fids)
                for i in range(len(fid_list)):
                    self.endpoint_connections[fid_list[i]["fid"]][fid_list[i]["type"]]=nodekeyIndex
            nodekeyIndex += 1
                    
        
        return self.endpoint_connections
    
    def analyze_intersections(self):
        """分析相交关系"""
        features = list(self.layer.getFeatures())
        
        for i, feat1 in enumerate(features):
            geom1 = feat1.geometry()
            fid1 = feat1.id()
            
            # 使用空间索引快速查找可能相交的要素
            bbox = geom1.boundingBox()
            candidate_ids = self.spatial_index.intersects(bbox)
            
            for candidate_id in candidate_ids:
                if candidate_id == fid1:
                    continue
                    
                # 获取候选要素
                feat2 = self.layer.getFeature(candidate_id)
                geom2 = feat2.geometry()
                
                # 检查是否相交
                if geom1.intersects(geom2):
                    intersection = geom1.intersection(geom2)
                    
                    if not intersection.isEmpty():
                        # 检查是否只是端点相接
                        if not self._is_only_endpoint_connection(geom1, geom2):
                            self.intersections[fid1].add(candidate_id)
                            self.intersections[candidate_id].add(fid1)
        
        return self.intersections
    
    def analyze_adjacent_lines(self, buffer_distance=1.0):
        """
        分析相邻（平行）线关系
        
        参数:
        buffer_distance: float - 缓冲距离，用于判断是否相邻
        """
        features = list(self.layer.getFeatures())
        
        for i, feat1 in enumerate(features):
            geom1 = feat1.geometry()
            fid1 = feat1.id()
            
            # 创建缓冲区
            buffer1 = geom1.buffer(buffer_distance, 5)  # 5个线段
            
            # 使用空间索引查找
            candidate_ids = self.spatial_index.intersects(buffer1.boundingBox())
            
            for candidate_id in candidate_ids:
                if candidate_id == fid1:
                    continue
                    
                feat2 = self.layer.getFeature(candidate_id)
                geom2 = feat2.geometry()
                
                # 检查是否在缓冲区内
                if geom2.intersects(buffer1):
                    # 排除直接相交的情况
                    if not geom1.intersects(geom2):
                        # 计算平均距离
                        avg_distance = self._calculate_avg_distance(geom1, geom2)
                        
                        if avg_distance <= buffer_distance:
                            self.adjacent_lines[fid1].add(candidate_id)
                            self.adjacent_lines[candidate_id].add(fid1)
        
        return self.adjacent_lines
    
    def _point_key(self, point):
        """将点坐标转换为容差范围内的整数键"""
        x = round(point.x() / self.tolerance)
        y = round(point.y() / self.tolerance)
        return (x, y)
    
    def _is_only_endpoint_connection(self, geom1, geom2):
        """检查是否只是端点相接"""
        intersection = geom1.intersection(geom2)
        
        if intersection.isEmpty():
            return False
        
        if intersection.type() == QgsWkbTypes.PointGeometry:
            # 检查交点的数量
            if intersection.isMultipart():
                points = intersection.asMultiPoint()
                if len(points) > 1:
                    return False
                
                # 检查是否是端点
                point = points[0]
                endpoints1 = self._get_endpoints(geom1)
                endpoints2 = self._get_endpoints(geom2)
                
                is_endpoint1 = any(self._points_equal(point, ep) for ep in endpoints1)
                is_endpoint2 = any(self._points_equal(point, ep) for ep in endpoints2)
                
                return is_endpoint1 and is_endpoint2
        
        return False
    
    def _get_endpoints(self, geometry):
        """获取几何的所有端点"""
        endpoints = []
        
        if geometry.isMultipart():
            lines = geometry.asMultiPolyline()
            for line in lines:
                if len(line) >= 2:
                    endpoints.append(line[0])
                    endpoints.append(line[-1])
        else:
            line = geometry.asPolyline()
            if len(line) >= 2:
                endpoints.append(line[0])
                endpoints.append(line[-1])
        
        return endpoints
    
    def _points_equal(self, p1, p2):
        """判断两点是否在容差范围内相等"""
        return math.sqrt((p1.x()-p2.x())**2 + (p1.y()-p2.y())**2) <= self.tolerance
    
    def _calculate_avg_distance(self, geom1, geom2, sample_points=10):
        """计算两条线之间的平均距离"""
        points1 = self._sample_line(geom1, sample_points)
        points2 = self._sample_line(geom2, sample_points)
        
        total_distance = 0
        count = 0
        
        for p1 in points1:
            min_dist = float('inf')
            for p2 in points2:
                dist = math.sqrt((p1.x()-p2.x())**2 + (p1.y()-p2.y())**2)
                if dist < min_dist:
                    min_dist = dist
            
            if min_dist != float('inf'):
                total_distance += min_dist
                count += 1
        
        return total_distance / count if count > 0 else float('inf')
    
    def _sample_line(self, geometry, num_points):
        """在线几何上采样点"""
        points = []
        
        if geometry.isMultipart():
            lines = geometry.asMultiPolyline()
            for line in lines:
                points.extend(self._sample_polyline(line, num_points))
        else:
            line = geometry.asPolyline()
            points.extend(self._sample_polyline(line, num_points))
        
        return points
    
    def _sample_polyline(self, polyline, num_points):
        """在折线上采样点"""
        if len(polyline) < 2:
            return []
        
        # 计算总长度
        total_length = 0
        for i in range(len(polyline)-1):
            p1 = polyline[i]
            p2 = polyline[i+1]
            total_length += math.sqrt((p2.x()-p1.x())**2 + (p2.y()-p1.y())**2)
        
        if total_length == 0:
            return polyline
        
        points = []
        step = total_length / (num_points - 1)
        
        for i in range(num_points):
            target_length = i * step
            points.append(self._get_point_at_length(polyline, target_length))
        
        return points
    
    def _get_point_at_length(self, polyline, target_length):
        """获取折线上指定长度处的点"""
        accumulated = 0
        
        for i in range(len(polyline)-1):
            p1 = polyline[i]
            p2 = polyline[i+1]
            
            segment_length = math.sqrt((p2.x()-p1.x())**2 + (p2.y()-p1.y())**2)
            
            if accumulated + segment_length >= target_length or i == len(polyline)-2:
                # 目标点在这个线段上
                ratio = (target_length - accumulated) / segment_length if segment_length > 0 else 0
                ratio = max(0, min(1, ratio))  # 限制在0-1之间
                
                x = p1.x() + ratio * (p2.x() - p1.x())
                y = p1.y() + ratio * (p2.y() - p1.y())
                
                return QgsPoint(x, y)
            
            accumulated += segment_length
        
        # 如果目标长度超过总长度，返回最后一个点
        return polyline[-1]