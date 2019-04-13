
from fitlog.fastlog.log_read import StandbyStepLogReader
from fitlog.fastserver.server.utils import expand_dict

from collections import defaultdict

class ChartStepLogHandler:
    def __init__(self, save_log_dir, uuid, round_to=6, max_steps=400, wait_seconds=60,
                 exclude_columns=None):
        self.reader = StandbyStepLogReader(save_log_dir, uuid, wait_seconds)

        self._save_log_dir = save_log_dir
        self.uuid = uuid
        self.path2spath = {}
        self.max_steps = max_steps
        self.round_to = round_to

        if exclude_columns is None:
            exclude_columns = {}
        else:
            assert isinstance(exclude_columns, dict)
        self.exclude_columns = exclude_columns

    def update_logs(self, only_once=False):
        steps = self.reader.read_update(only_once)
        data = {}
        for key, values in steps.items():# key为loss, metric, value为[{'step':, epoch:, loss:{}}]
            # [{'step':, epoch:, metric:{}}]
            if key!='finish':
                if key in self.path2spath:
                    path2spath = self.path2spath[key]
                else:
                    first_record = values[0][key]  # 记录的内容
                    path2spath = self.path2shortpath(first_record)
                    self.path2spath[key] = path2spath
                expanded_values = defaultdict(list)
                for v in values:
                    expand_v = {}
                    real_v = v[key]
                    for _key in ['step', 'epoch']:
                        if _key in v:
                            expand_v[_key] = v[_key]
                    _expand_v = expand_dict('', real_v)
                    for __key in list(_expand_v.keys()): # 删除不需要的图
                        if __key in self.exclude_columns:
                            _expand_v.pop(__key)
                    for i_key, i_value in _expand_v.items():
                        if isinstance(i_value, (float, int)):
                            short_i_key = path2spath[i_key]
                            i_value = round(i_value, self.round_to)
                            i_expand_v = expand_v.copy()
                            i_expand_v['name'] = short_i_key
                            i_expand_v['value'] = i_value
                            expanded_values[short_i_key].append(i_expand_v)

                l_expanded_values = []
                for i_key in list(expanded_values.keys()):
                    i_value = expanded_values[i_key]
                    if len(i_value)>self.max_steps: # 不能超过一定的step
                        l_expanded_values.extend(i_value[-self.max_steps:])
                    else:
                        l_expanded_values.extend(i_value)
                data[key] = l_expanded_values
            else:
                data[key] = values
        return data

    def path2shortpath(self, _dict):
        """
        比如两个value的path
            dev-BMESMetric-f1
            dev-BMESMEtric-pre
            test-BMESMetric-f1
        缩写为, 从最小删除到最大
            dev-f1
            dev-pre
            test-f1

        :param _dict: {'expanded_path': 'short_path'}
        :return:
        """
        paths = _get_dict_path(_dict)
        path2spath = _refine_path(paths)
        return path2spath

def _get_dict_path(_dict, paths=None):
    # 给定一个dict, 返回所有的path，path以[[path], []]展示. 内容存到container中
    if paths==None:
        paths = []
    else:
        paths = paths.copy()
    new_paths = []
    for key, value in _dict.items():
        if isinstance(value, dict):
            _paths = _get_dict_path(value, paths + [key])
            new_paths.extend(_paths)
        else:
            new_paths.append(paths + [key])
    return new_paths

def _refine_path(paths):
    """
    给定list的path，将公共的部分删掉一些. 这里只处理完全一样深度的metric. 主要为了删除相同的metric_name
        [['metric', 'BMESF1MEtric', 'f1'], ['metric', 'BMESF1Metric'], ...]
    :param paths:
    :return:
    """
    if len(set(map(len, paths)))!=1 or len(paths)==1:# 如果深度不同直接回去
        path2shortpath = {'-'.join(path):'-'.join(path) for path in paths}
    else:
        delete_depths = []
        for depth in range(len(paths[0])):
            names = set()
            for path in paths:
                names.add(path[depth])
            if len(names)==1:
                delete_depths.append(depth)
        for i in range(len(paths)):
            for d in reversed(delete_depths):
                paths[i].pop(d)
        path2shortpath = {'-'.join(path): '-'.join(path) for path in paths}
    return path2shortpath

if __name__ == '__main__':
    a = {'test':{'F1SpanMetric': {'f1': 0.3606739335382445, 'pre': 0.6220669896180324}}, 'dev':{'F1SpanMetric': {'f1': 0.45963128728272284, 'pre1': 0.25299515839718356}}}

    paths = _get_dict_path(a)
    print(paths)
    print(_refine_path(paths))

    print(expand_dict('', a))
