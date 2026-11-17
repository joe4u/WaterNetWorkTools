__author__ = 'CJQiao'
__date__ = '2022-08-03'
__copyright__ = '(C) 2022 by CJQiao'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from asyncio.windows_events import NULL
from contextlib import nullcontext
from typing import List, Tuple

from requests import NullHandler
from qgis.core import (QgsFeature,QgsVectorLayer)

class WaterNetwork:
    @staticmethod
    def meetCircle(meetindex,lastindex,line,feedback):
        
        endLines=[]
        circleline=[]
        
        meetFeature=line.getFeature(int(meetindex))
        if(meetFeature["isreverse"]=="f"):
            endLines=meetFeature["source"].split(",")
        else:
            endLines=meetFeature["target"].split(",")
        # feedback.pushInfo('endnode#: {0}.'.format(','.join('%s'%id for id in endnode)))

        circleline.append(int(meetindex))
        circleline.append(int(lastindex))
        # feedback.pushInfo('start circleline#: {0}.'.format(','.join('%s'%id for id in circleline)))
        while(str(circleline[-1]) not in endLines):
            feedback.pushInfo('circle[-1]-endlines#: {0}-{1}.'.format(str(circleline[-1]),endLines))
            if feedback and feedback.isCanceled():
                break
            currentFeature=line.getFeature(int(circleline[-1]))
            if(currentFeature["isreverse"]=="f"):
                canidate=[item for item in currentFeature["source"].split(",") if item]
            else:
                canidate=[item for item in currentFeature["target"].split(",") if item]
            # feedback.pushInfo("hasBir:{0}".format([line.getFeature(int(item))["isreverse"]=="b" for item in canidate]))
            # if any([line.getFeature(int(item))["isreverse"]=="b" for item in canidate]):
            #     break
                # canidatefeature=line.getFeature(int(item))
                # if(canidatefeature["isreverse"]=="b"):
                #         break
            for item in canidate:
                if(item=="" or item == "-999"):
                    continue
                canidatefeature=line.getFeature(int(item))                
                if((canidatefeature["isreverse"]=="f" and (str(circleline[-1]) in canidatefeature["target"].split(",")))
                   or (canidatefeature["isreverse"]=="t" and (str(circleline[-1]) in canidatefeature["source"].split(",")))):
                    circleline.append(int(item))
        return  circleline       
    
        
    @staticmethod
    def InitDir1(index,line:QgsVectorLayer,closedlineIds,feedback,flag='u'):
        #深度优先遍历-2接连环
        cur_node_stack=index
        finished_stack=[]
        all_circleline=[]
        all_line_count=line.featureCount()
        while(len(cur_node_stack)>0):
            if feedback.isCanceled():
                break
            curindex=cur_node_stack.pop()
            if curindex in finished_stack:
                continue
            finished_stack.append(curindex)          
            currentFeature=line.getFeature(int(curindex))
            # feature_ids=[]
            if(currentFeature["isreverse"]=="f"):
                feature_ids=currentFeature["target"].split(",")
            elif(currentFeature["isreverse"]=="t"):
                feature_ids=currentFeature["source"].split(",")

            for featureid in feature_ids:
                if(featureid=="" or featureid == "-999"):
                    continue
                
                feature=line.getFeature(int(featureid))
                # feedback.pushInfo('featureid#: {0}.'.format(featureid))
                if(feature["isOpen"]==False):
                    continue

                # feedback.pushInfo('featureid-curindex#: {0}-{1}-{2}.'.format(featureid,cur_node_stack,finished_stack))
                if(int(featureid) not in cur_node_stack+finished_stack):
                    if(feature["isreverse"]!=flag):
                        continue
                    feature_source_ids=feature["source"].split(",")
                    if(str(curindex) in feature_source_ids):
                        feature["isreverse"]="f"
                    else:
                        feature["isreverse"]="t"
                    line.updateFeature(feature)

                    cur_node_stack.append(int(featureid))
                else:
                    #环  参数curindex line
                    # if(str(featureid) in cur_node_stack):
                    #     cur_node_stack.remove(str(featureid))
                        # finished_stack.append(str(featureid))
                    # if(line.getFeature(int(featureid))["isreverse"]=="b"):
                        # finished_stack.append(str(featureid))
                        # continue
                    feedback.pushInfo('featureid-curindex#: {0}-{1}.'.format(featureid,curindex))
                    # loopindexs=WaterNetwork.meetCircle(featureid,curindex,line,feedback)
                    # feedback.pushInfo('loopindexs#: {0}.'.format(loopindexs))
                    # finished_stack+=loopindexs
                    # all_circleline+=loopindexs
            
            feedback.setProgress(int(len(finished_stack)*100/all_line_count))
        all_circleline=list(set(all_circleline))
        for item in all_circleline:
            feature=line.getFeature(int(item))
            feature["isreverse"]="b"
            line.updateFeature(feature)
    @staticmethod
    def InitDir(index,line:QgsVectorLayer,closedlineIds,feedback,flag='u'):
        #深度优先遍历-2接连环
        cur_node_stack=index  # (当前节点, 路径)
        pathdict={str(index[0]):{int(index[0])}}
        finished_stack=[]
        all_circleline=set()
        all_line_count=line.featureCount()
        while(len(cur_node_stack)>0):
            if feedback.isCanceled():
                break
            curindex=cur_node_stack.pop()
            
            if curindex in finished_stack:
                continue
            finished_stack.append(curindex)          
            currentFeature=line.getFeature(int(curindex))
            # feature_ids=[]
            if(currentFeature["isreverse"]=="f"):
                feature_ids=currentFeature["target"].split(",")
            elif(currentFeature["isreverse"]=="t"):
                feature_ids=currentFeature["source"].split(",")

            for featureid in feature_ids:
                if(featureid=="" or featureid == "-999"):
                    continue
                
                feature=line.getFeature(int(featureid))
                # feedback.pushInfo('featureid#: {0}.'.format(featureid))
                if(feature["isOpen"]==False):
                    continue

                # feedback.pushInfo('featureid-curindex#: {0}-{1}-{2}.'.format(featureid,cur_node_stack,finished_stack))
                if(int(featureid) not in cur_node_stack+finished_stack):
                    if(feature["isreverse"]!=flag):
                        continue
                    feature_source_ids=feature["source"].split(",")
                    if(str(curindex) in feature_source_ids):
                        feature["isreverse"]="f"
                    else:
                        feature["isreverse"]="t"
                    line.updateFeature(feature)

                    cur_node_stack.append(int(featureid))

                    pathdict[str(featureid)]=pathdict[str(curindex)]|{int(featureid)}
                    # feedback.pushInfo('pathdict-curindex#: {0}.'.format(pathdict[str(curindex)]))
                else:
                    #环  参数curindex line
                    if(int(featureid) in cur_node_stack):
                        cur_node_stack=[item for item in cur_node_stack if item != int(featureid)]
                        # finished_stack.append(str(featureid))
                    # if(line.getFeature(int(featureid))["isreverse"]=="b"):
                        # finished_stack.append(str(featureid))
                        # continue
                    # feedback.pushInfo('featureid-curindex#: {0}-{1}.'.format(featureid,curindex))
                    # feedback.pushInfo('path1-paht2#: {0}-{1}.'.format(pathdict[str(featureid)],pathdict[str(curindex)]))
                    loopindexs=pathdict[str(featureid)]^pathdict[str(curindex)]
                    # loopindexs=WaterNetwork.meetCircle(featureid,curindex,line,feedback)
                    # feedback.pushInfo('loopindexs#: {0}.'.format(loopindexs))
                    # finished_stack+=loopindexs
                    all_circleline|=loopindexs
            
            feedback.setProgress(int(len(finished_stack)*100/all_line_count))
        # all_circleline=list(all_circleline)
        for item in all_circleline:
            feature=line.getFeature(int(item))
            feature["isreverse"]="b"
            line.updateFeature(feature)
    @staticmethod
    def getDownStream(index,line,feedback):
        downStreamIndexes=[index]
        cur_feature_stack=[index]
        finished_stack=[]
        while(len(cur_feature_stack)>0):
            if feedback.isCanceled():
                break
            cur_featureid=cur_feature_stack.pop()
            if(cur_featureid in finished_stack):
                continue
            finished_stack.append(cur_featureid)
            feature=line.getFeature(cur_featureid)
            # feedback.pushInfo('cur_featureid#: {0}.'.format(cur_featureid))
            idxs=[]
            if(feature["isreverse"]=="f"):
                idxs=[int(item) for item in feature["target"].split(",") if item != ""]
            elif(feature["isreverse"]=="t"):
                idxs=[int(item) for item in feature["source"].split(",") if item != ""]
            elif(feature["isreverse"]=="b"):
                idxs=[int(item) for item in feature["source"].split(",") if item != ""]
                idxs+=[int(item) for item in feature["target"].split(",") if item != ""]
            for idx in idxs:
                if(idx in finished_stack):
                    continue
                downfeature=line.getFeature(idx)
                # if(str(cur_featureid) in downfeature["source"].split(",")):
                #     downfeature["isreverse"]="f"
                # else:
                #     downfeature["isreverse"]="t"
                line.updateFeature(downfeature)
                # downStreamIndexes+=idxs
                cur_feature_stack.append(idx)
        
        return list(set(finished_stack))
    @staticmethod
    def getUpStream(index,line,feedback):
        # upStreamIndexes=[index]
        cur_feature_stack=[index]
        finished_stack=[]
        while(len(cur_feature_stack)>0):
            if feedback.isCanceled():
                break
            cur_featureid=cur_feature_stack.pop()
            if(cur_featureid in finished_stack):
                continue
            finished_stack.append(cur_featureid)
            feature=line.getFeature(cur_featureid)
            idxs=[]
            if(feature["isreverse"]=="f"):
                idxs=[int(item) for item in feature["source"].split(",") if item != ""]
            elif(feature["isreverse"]=="t"):
                idxs=[int(item) for item in feature["target"].split(",") if item != ""]
            elif(feature["isreverse"]=="b"):
                idxs=[int(item) for item in feature["source"].split(",") if item != ""]
                idxs+=[int(item) for item in feature["target"].split(",") if item != ""]
            for idx in idxs:
                if(idx in finished_stack):
                    continue
                if(idx==-999):
                    break
                upfeature=line.getFeature(idx)
                # feedback.pushInfo('upfeature#: {0}-{1}.'.format(idx,upfeature))
                if((str(cur_featureid) in upfeature["target"].split(",") and upfeature["isreverse"]=="f")
                   or (str(cur_featureid) in upfeature["source"].split(",") and upfeature["isreverse"]=="t")):
                    cur_feature_stack.append(idx)
                elif(upfeature["isreverse"]=="b"):
                    cur_feature_stack.append(idx)
                
                # upStreamIndexes+=idxs
                    
        
        return list(set(finished_stack))
    @staticmethod
    def findLoopStartEnd(index,line,feedback):
        firstLine=line.getFeature(index)
        ufeature_idxs=firstLine["source"].split(",")
        dfeature_idxs=firstLine["target"].split(",")
        endidx=-999
        startidx=-999
        e_canidaty_idxs=[]
        s_canidaty_idxs=[]
        for ufeature_idx in ufeature_idxs:
            if(ufeature_idx==""):
                continue
            ufeature=line.getFeature(int(ufeature_idx))
            if((str(index) in ufeature["target"].split(",") and ufeature["isreverse"] in ["f","b"])
               or (str(index) in ufeature["source"].split(",") and ufeature["isreverse"] in ["t","b"])):
                endidx=int(ufeature_idx)
                e_canidaty_idxs.append(int(ufeature_idx))
        for dfeature_idx in dfeature_idxs:
            if(dfeature_idx==""):
                continue
            dfeature=line.getFeature(int(dfeature_idx))
            if((str(index) in dfeature["target"].split(",") and dfeature["isreverse"] in ["f","b"])
               or (str(index) in dfeature["source"].split(",") and dfeature["isreverse"] in ["t","b"])):
                startidx=int(dfeature_idx)
                s_canidaty_idxs.append(int(ufeature_idx))
        return startidx,endidx,s_canidaty_idxs,e_canidaty_idxs

    #打开水源
    @staticmethod
    def setDownStraamDirOpen(index,line,feedback):
        firstLine=line.getFeature(index)
        firstLine["isOpen"]=True
        line.updateFeature(firstLine)
        feature=QgsFeature()
        if(firstLine["isreverse"]=='u'):
            upFeatureIds=[item for item in firstLine["source"].split(",") if item != ""]
            downFeatureIds=[item for item in firstLine["target"].split(",") if item != ""]
            sourceHasWater=False
            targetHasWater=False
            for upFeatureId in upFeatureIds:
                feature=line.getFeature(int(upFeatureId))
                if(feature['isreverse']!='u'):
                    sourceHasWater=True
                    break
            for downFeatureId in downFeatureIds:
                feature=line.getFeature(int(downFeatureId))
                if(feature['isreverse']!='u'):
                    targetHasWater=True
                    break
            # sourceHasWater=
            # targetHasWater=
            #打开后形成环
            if(sourceHasWater and targetHasWater):
                start_idx,end_idx,s_canidate_indexs,e_canidate_indexs=WaterNetwork.findLoopStartEnd(index,line,feedback)
                loops=WaterNetwork.shortest_path_dijkstra(start_idx,end_idx,line,feedback,[index])[0]
                forSureFirst=line.getFeature(loops[0])
                forSureLast=line.getFeature(loops[-1])
                
                s_first_indexs=set([int(item) for item in forSureFirst["source"].split(",") if item != ""])
                t_first_indexs=set([int(item) for item in forSureFirst["target"].split(",") if item != ""])
                s_last_indexs=set([int(item) for item in forSureLast["source"].split(",") if item != ""])
                t_last_indexs=set([int(item) for item in forSureLast["target"].split(",") if item != ""])
                
                newloop=loops.copy()
                newloop.append(index)
                loopset=set(newloop)
                if(len(s_first_indexs.intersection(loopset))>1 or len(t_first_indexs.intersection(loopset))>1):
                    loops.remove(loops[0])
                if(len(s_last_indexs.intersection(loopset))>1 or len(t_last_indexs.intersection(loopset))>1):
                    loops.remove(loops[-1])
                loops.append(index)



                for fid in loops:
                    feature=line.getFeature(int(fid))
                    feature["isreverse"]="b"
                    line.updateFeature(feature)
                # line.removeSelection()
                # line.selectByIds(loops) 
                # feedback.pushInfo('loops#: {0}.'.format(','.join('%s'%id for id in loops)))
            elif(sourceHasWater):
                # index=firstLine["source"]
                firstLine["isreverse"]="f"
                line.updateFeature(firstLine)
                WaterNetwork.InitDir([index],line,[-999],feedback)
            elif(targetHasWater):
                # index=firstLine["target"]
                firstLine["isreverse"]="t"
                line.updateFeature(firstLine)
                WaterNetwork.InitDir([index],line,[-999],feedback)
            else:
                return
        #人为改动网络
        else:
            return
    #pathnode to pahtedge
        #单向流关闭
    @staticmethod
    def singleDirClose(firstLine,line,feedback):
        downIds=WaterNetwork.getDownStream(firstLine.id(),line,feedback)
        for downId in downIds:
            downLine=line.getFeature(downId)
            downLine["isreverse"]="u"
            line.updateFeature(downLine)
    @staticmethod
    def shortest_path_dijkstra(start_id, end_id, line,feedback,exclude=[]) -> Tuple[List[str], int]:
        """
        使用Dijkstra算法查找最短路径（可以处理带权重的扩展）
        返回: (路径列表, 路径长度)
        """
        features=line.getFeatures("isOpen=true")
        nodes=[node.id() for node in features]
        if start_id == end_id:
            return [start_id], 0
        # 初始化距离和前驱节点
        distances = {node: float('inf') for node in nodes}
        distances[start_id] = 0
        predecessors = {}
        unvisited = set(nodes)
        
        while unvisited:
            # 选择未访问节点中距离最小的
            current = min(unvisited, key=lambda x: distances[x])
            
            # 如果当前节点距离是无穷大，说明不可达
            if distances[current] == float('inf'):
                break
            currentFeature=line.getFeature(int(current))
            current_adjacency=[int(item) for item in
                currentFeature["source"].split(",")+currentFeature["target"].split(",") if item]
            current_adjacency=list(filter(lambda x:x not in exclude,current_adjacency))
            # 更新邻居节点的距离
            for neighbor in current_adjacency:
                if neighbor in unvisited:
                    new_distance = distances[current] + 1  # 这里权重为1
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        predecessors[neighbor] = current
            
            unvisited.remove(current)
            
            # 如果已经处理到终点，可以提前结束
            if current == end_id:
                break
        
        # 如果终点不可达
        if distances[end_id] == float('inf'):
            return [], -1
        
        # 回溯构建路径
        path = []
        current = end_id
        while current in predecessors:
            path.append(current)
            current = predecessors[current]
        path.append(start_id)
        path.reverse()
        
        return path, distances[end_id]
    @staticmethod
    def shortest_path_BFS(start_id, end_id, line,feedback,exclude=[]) -> Tuple[List[str], int]:
        """
        查找包含边(u,v)的最短环
        """
        from collections import deque        
        # BFS从u到v找最短路径
        queue = deque([(start_id, [start_id])])  # (当前节点, 路径)
        visited = {start_id}
        
        shortest_path = None
        
        while queue:
            node, path = queue.popleft()
            
            if node == end_id:
                shortest_path = path
                break
            currentFeature=line.getFeature(int(node))
            current_adjacency=[int(item) for item in
                currentFeature["source"].split(",")+currentFeature["target"].split(",") if item]
            current_adjacency=list(filter(lambda x:x not in exclude,current_adjacency))
            for neighbor in current_adjacency:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        # 恢复边
        # graph[u].append(v)
        # graph[v].append(u)
        
        if shortest_path:
            # 最短路径 + 边(u,v) = 最短环
            return shortest_path,len(shortest_path)
        
        return None,None          
    #双向关闭
    @staticmethod
    def biDirClose(firstLine,line,feedback):

        firstLine["isOpen"]=False
        firstLine["isreverse"]="u"
        line.updateFeature(firstLine)
        cur_feature_stack=[firstLine.id()]
        isfinded=False
       
        finishedline=[]
        upnodeIndex=-999
        while(len(cur_feature_stack)>0):
            if isfinded:
                break
            curnode=cur_feature_stack.pop()
            if(curnode in finishedline):
                continue
            finishedline.append(curnode)
            feature=line.getFeature(curnode)
            str_idxs=feature["source"].split(",")+feature["target"].split(",")
            idxs=[int(idx) for idx in str_idxs if idx!=""]
            for idx in idxs:
                if(idx in finishedline):
                    continue
                upfeature=line.getFeature(idx)
                if(upfeature["isreverse"]=="b"):
                    cur_feature_stack.append(idx)
                elif(upfeature["isreverse"]=="f"):
                    if(str(curnode) in upfeature["target"].split(",")):
                        upnodeIndex=idx
                        isfinded=True
                        break
                elif(upfeature["isreverse"]=="t"):
                    if(str(curnode) in upfeature["source"].split(",")):
                        upnodeIndex=idx
                        isfinded=True
                        break
                else:
                    continue   
            # feedback.pushInfo('curnodes#: {0}.'.format(curnodes))
        if(upnodeIndex==-999):
            return
        # feedback.pushInfo('upnodeIndex#: {0}.'.format(upnodeIndex))
        
        WaterNetwork.InitDir([upnodeIndex],line,[],feedback,"b")
    #关闭水源
    @staticmethod
    def setDownStraamDirClose(index,line,feedback):
        firstLine=line.getFeature(index)
        firstLine["isOpen"]=False
        line.updateFeature(firstLine)
        #断点为单流，下游全部设为u
        if(firstLine["isreverse"]=="f" or firstLine["isreverse"]=="t"):
            WaterNetwork.singleDirClose(firstLine,line,feedback) 
        #断点为双流
        elif(firstLine["isreverse"]=="b"):
            WaterNetwork.biDirClose(firstLine,line,feedback)
        else:
            return
    @staticmethod    
    def setDownStreamDir(index,line,isopen,feedback):
        if isopen:            
            #打开水源
            WaterNetwork.setDownStraamDirOpen(index,line,feedback)
        else:
            #关闭水源
            WaterNetwork.setDownStraamDirClose(index,line,feedback)