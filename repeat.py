#!/usr/bin/python3
# coding=utf-8
# -*- coding：utf-8 -*-
import json
import os
import re

# 排除的目录
ExcludeDir = ['build', '.idea', 'target', '.gradle', 'lib', '.git', 'gradle', 'assets']

# 所有非文件资源统计,0位置代表字符串资源，1位置代表color资源，2位置为自定义属性资源，3位置代表style资源，4位置代表dimen资源
NotFileResource = [{}, {}, {}, {}, {}]


class RepeatWrapper:
    # 重复路径
    path = []

    def __init__(self, ):
        self.path = []


def get_all_module_path(cur_path: str) -> list:
    """
    获取某个路径下所有module
    :param cur_path:  路径
    :return: 路径的绝对地址的list
    """

    global ExcludeDir
    module_path_list = []
    for file in os.listdir(cur_path):
        if file.startswith('.'):
            # 以。开头的目录都要跳过
            continue
        if file in ExcludeDir:
            continue
        this_file_path = os.path.join(cur_path, file)
        if os.path.exists(os.path.join(this_file_path, "src")) and os.path.exists(
                os.path.exists(os.path.join(this_file_path, "build.gradle"))):
            module_path_list.append(this_file_path)
            # 当前module下仍然有可能有其他module
            module_path_list.extend(get_all_module_path(this_file_path))
        elif os.path.isdir(this_file_path):
            module_path_list.extend(get_all_module_path(this_file_path))
    return module_path_list


# 获取某个文件路径下所有资源
def get_all_not_file_resource_for_file(path):
    str_lists = []
    str_file = open(path, 'r')
    resource_pat = re.compile('name\s*=\s*"([^\s]*)\s*"[\s>/]')
    for line in str_file:
        if line.find("<item") != -1:
            continue
        if line.find("<enum") != -1:
            continue
        if line.lstrip().startswith("<!--"):
            continue
        res = resource_pat.findall(line)
        if len(res) != 0:
            str_lists.extend(res)
    return str_lists


def get_all_not_file_resource_for_module(module_path: str) -> dict:
    """
    获取某个module下的所有非文件资源名称

    :param module_path:  某个module的路径
    :return: 返回一个list，0位置代表字符串资源，1位置代表color资源，2位置为自定义属性资源，3位置代表style资源，4位置代表dimen资源
    """
    possible_path = ["strings.xml", "string.xml", "colors.xml", "color.xml", "attr.xml",
                     "attrs.xml", "style.xml", "styles.xml", "dimen.xml", "dimens.xml"]

    key_names = ["string", "color", "attr", "style", "dimen"]
    resource_res = {"string": [], "color": [], "attr": [], "style": [], "dimen": []}
    for index in range(len(possible_path)):
        path = possible_path[index]
        resource_file_path = module_path + '/src/main/res/values/' + path
        if not os.path.exists(resource_file_path):
            continue
        # 获取所有要修改的字符的名称
        resources_names = get_all_not_file_resource_for_file(resource_file_path)
        key_name = key_names[index // 2]
        resource_res[key_name].extend(resources_names)
    return resource_res


def get_all_not_file_resource(path: str) -> dict:
    """
    获取某个项目的所有非文件资源分布情况
    :param path:  项目根目录
    :return: 返回一个dict结构，包含 string,color,attr,style,dimen
    具体示例如下：
    {
        string:{
            normal_spacing_top:[
                "/home/jianglei/AndroidStudioProjects/temp/ManagerWidget",
                "/home/jianglei/AndroidStudioProjects/temp/ManagerWidgetTemp"
            ],
            op_activity_horizontal_margin:[
                "/home/jianglei/AndroidStudioProjects/temp/ManagerWidget",
                "/home/jianglei/AndroidStudioProjects/temp/ManagerName"
            ],
        },
        ……
    }
    """
    not_file_resource = {"string": {}, "color": {}, "attr": {}, "style": {}, "dimen": {}}
    modules = get_all_module_path(path)
    for module in modules:
        # 获取某个module的所有非文件资源
        resources_dict = get_all_not_file_resource_for_module(module)
        all_keys = not_file_resource.keys()
        for k in all_keys:
            key_dict = not_file_resource[k]
            for resource_name in resources_dict[k]:
                if key_dict.get(resource_name) is None:
                    key_dict[resource_name] = [module]
                else:
                    repeat_names = key_dict[resource_name]
                    repeat_names.append(module)
    return not_file_resource


def get_all_file_resource_for_dir(dir_path: str):
    """
    获取某个资源文件夹下所有资源文件的名称

    :param dir_path:  资源文件夹名称,比如 ×××/src/main/res/anim
    :return:  该文件夹下所有的资源文件名称
    """
    res = []
    # 遍历该资源文件夹
    for res_file in os.listdir(dir_path):
        if os.path.isdir(res_file):
            # 如果该资源文件夹下还有文件夹，忽略
            continue
        res.append(res_file)
    return res


def get_all_file_resource_for_module(module_path: str) -> dict:
    """
    获取某个module的所有文件资源名称
    :param module_path: module的路径
    :return: 返回一个dict，key 分别为drawable, layout, anim, menu,mipmap ，每个key分别对应一个list，保存的是对应类别的资源文件名称
    """

    res = {"drawable": [], "layout": [], "anim": [], "menu": [], "mipmap": []}
    value_dirs = res.keys()
    resource_path = module_path + "/src/main/res"
    if not os.path.exists(resource_path):
        return res
    for file in os.listdir(resource_path):
        cur_file_path = os.path.join(resource_path, file)
        if not os.path.isdir(cur_file_path):
            continue
        for value_dir in value_dirs:
            if file.startswith(value_dir):
                res[value_dir].extend(get_all_file_resource_for_dir(cur_file_path))
                # 由于不同尺寸等文件夹存在，这里需要去重
                res[value_dir] = list(set(res[value_dir]))

    return res


def get_all_file_resources(dir_path: str) -> dict:
    """
    获取某个项目的所有文件资源分布情况，包括layout，drawable,layout,anim,menu,mipmap
    :param dir_path: 项目根目录
    :return: 返回一个dict，key 分别为drawable, layout, anim, menu,mipmap ， 具体结构如下所示
    {
        drawable:{
            normal_spacing_top:[
                "/home/jianglei/AndroidStudioProjects/temp/ManagerWidget",
                "/home/jianglei/AndroidStudioProjects/temp/ManagerWidgetTemp"
            ],
            op_activity_horizontal_margin:[
                "/home/jianglei/AndroidStudioProjects/temp/ManagerWidget",
                "/home/jianglei/AndroidStudioProjects/temp/ManagerName"
            ],
        },
        ……
    }
    """
    res = {"drawable": {}, "layout": {}, "anim": {}, "menu": {}, "mipmap": {}}

    modules = get_all_module_path(dir_path)
    for module in modules:
        # 获取某个module的所有非文件资源
        resources_dict = get_all_file_resource_for_module(module)
        all_keys = res.keys()
        for k in all_keys:
            key_dict = res[k]
            for resource_name in resources_dict[k]:
                if key_dict.get(resource_name) is None:
                    key_dict[resource_name] = [module]
                else:
                    repeat_names = key_dict[resource_name]
                    repeat_names.append(module)
    return res


def convert_to_builtin_type(repeat_wrapper: RepeatWrapper):  # 把MyObj对象转换成dict类型的对象
    d = {}
    d.update(repeat_wrapper.__dict__)
    return d


def print_repeat_resource(all_resource: dict):
    """
    打印资源的重复情况
    :all_resource 资源分布情况
    :return:  无
    """
    res = all_resource
    keys = res.keys()
    for key in list(keys):
        resource_keys = res[key].keys()
        for resource_key in list(resource_keys):
            if len(res[key][resource_key]) <= 1:
                del res[key][resource_key]
                continue
            res[key][resource_key].sort()

    print(json.dumps(all_resource, default=convert_to_builtin_type, indent=4))


try:
    file_path = os.path.abspath(os.path.curdir)
    print("以下是非文件资源")
    real_res = get_all_not_file_resource(file_path)
    print_repeat_resource(real_res)
    print("\n\n 以下是文件资源")
    real_res = get_all_file_resources(file_path)
    print_repeat_resource(real_res)

except KeyboardInterrupt:
    pass
