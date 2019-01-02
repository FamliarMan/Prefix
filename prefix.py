#!/usr/bin/python3
# coding=utf-8
# -*- coding：utf-8 -*-
import sys
import getopt
import re
import os
import fileinput

# 排除的目录
ExcludeDir = ['build', '.idea', 'target', '.gradle', 'lib', '.git', 'gradle', 'assets']

# 需要处理的模块
WorkModule = []

# 需要添加的前缀
Prefix = ""

# 输出日志
LogFile = None

# 当前是否是修复模式
IsFix = False

# 项目根目录
RootDir = ""

# 所有module路径
AllModulePath = []

# 当前要修改的module名称
NeedChangeModule = ""


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


def get_module_path(module: str) -> str:
    """
    获取某个module的路径
    :param module:  module的名称
    :return: 该module的绝对路径,如果没有返回空字符串
    """
    global AllModulePath
    for path in AllModulePath:
        if path.endswith(module):
            return path

    return ""


''''''''''''''''''''''''''''''''''' 以下是非文件资源的重命名方法'''''''''''''''''''''''''''''


# 重命名非文件资源
def rename_not_file():
    global LogFile, Prefix, NeedChangeModule
    possible_path = ["strings.xml", "string.xml", "colors.xml", "color.xml", "attr.xml",
                     "attrs.xml", "style.xml", "styles.xml", "dimen.xml", "dimens.xml"]
    # possible_path = ["strings.xml"]

    has_resource_file = False
    this_module_path = get_module_path(NeedChangeModule)
    for path in possible_path:
        resource_file_path = this_module_path + '/src/main/res/values/' + path
        if not os.path.exists(resource_file_path):
            continue
        has_resource_file = True
        # 获取所有要修改的字符的名称
        str_resources = get_not_file_resources(resource_file_path)
        for s in str_resources:
            if s.startswith(Prefix):
                continue
            log(s, None, None)
            # 找到该资源上层的每一个模块，分别修改
            for mod in WorkModule:
                # 获取该模块的绝对路径
                module_path = get_module_path(mod)
                if module_path == "":
                    continue
                log(s, mod, None)
                xml_pat, layout_pat, java_pat = get_not_file_pattern(resource_file_path, s)
                rename_not_file_dir(module_path, s, mod, xml_pat, layout_pat, java_pat)

    if not has_resource_file:
        print("No string.xml in this module")

    return


# 修改某个目录的非文件资源名称，比如字符串，颜色
def rename_not_file_dir(dir_path, resource_name, module_name, xml_pat, layout_pat, java_pat):
    if not os.path.isdir(dir_path):
        return
    global ExcludeDir
    for file in os.listdir(dir_path):
        cur_path = dir_path + "/" + file
        if os.path.isdir(cur_path) and file not in ExcludeDir:
            rename_not_file_dir(cur_path, resource_name, module_name, xml_pat, layout_pat, java_pat)
        elif not os.path.isdir(cur_path):
            # 只处理xml和java文件
            if file.endswith(".xml") or file.endswith(".java"):
                # if cur_path.find("/res/value") != -1 and cur_path.find(os.path.abspath(os.path.curdir)) == -1:
                #     continue
                rename_not_file_file(cur_path, resource_name, module_name, xml_pat, layout_pat, java_pat)


# 修改某个文件的非文件串资源名称
def rename_not_file_file(file_path, resource_name, module_name, xml_pat, layout_pat, java_pat):
    global Prefix, LogFile
    for line in fileinput.input(file_path, inplace=1):
        if file_path.endswith(".java"):
            # 对于java文件
            if line.startswith("//") or line.startswith("/*"):
                # 跳过注释行
                print(line, end="")
            elif java_pat.search(line) is None:
                # 跳过不包含目标的行
                print(line, end="")
            else:
                if java_pat.groups == 6:
                    # 对于attr要特殊处理
                    line = java_pat.sub('\g<1>\g<4>' + Prefix + resource_name + '\g<3>\g<6>', line)
                else:
                    line = java_pat.sub('\g<1>' + Prefix + resource_name + '\g<3>', line)
                print(line, end="")
                log(resource_name, module_name, os.path.basename(file_path))

        elif file_path.endswith(".xml"):
            if file_path.find("src/main/res/values") != -1:
                # 该xml文件是非layout,drawable文件,一般是string.xml,color.xml等文件
                if line.lstrip().startswith("<!--"):
                    # 跳过注释行
                    print(line, end="")
                    continue
                elif line.find("<item") == -1 and xml_pat.search(line) is None:
                    # 跳过不包含目标的行
                    print(line, end="")
                elif line.find("<item") != -1 and layout_pat.search(line) is None:
                    # 跳过不包含目标的行
                    print(line, end="")
                elif line.find("<item") == -1 and file_path.find(os.path.abspath(os.path.curdir)) == -1:
                    # 非本module下的非<item>项忽略
                    print(line, end="")
                else:
                    if line.find("<item") != -1:
                        # 对于item项，应该使用layout_xml规则

                        line = layout_pat.sub('\g<1>' + Prefix + resource_name + '\g<3>', line)
                    else:
                        line = xml_pat.sub('\g<1>' + Prefix + resource_name + '\g<3>', line)
                    print(line, end="")
                    log(resource_name, module_name, os.path.basename(file_path))
            else:
                # 对于layout和drawable中的xml文件
                if line.lstrip().startswith("<!--"):
                    # 跳过注释行
                    print(line, end="")
                elif layout_pat.search(line) is None:
                    # 跳过不包含目标的行
                    print(line, end="")
                else:
                    if layout_pat.groups == 5:
                        # 对于attr在xml中的要特殊对待
                        line = layout_pat.sub('\g<1>\g<2>' + Prefix + resource_name + '\g<4>', line)
                    else:
                        line = layout_pat.sub('\g<1>' + Prefix + resource_name + '\g<3>', line)
                    print(line, end="")
                    log(resource_name, module_name, os.path.basename(file_path))

    fileinput.close()


# 获取非文件资源的正则匹配规则
def get_not_file_pattern(file_path, resource_name):
    if file_path.find("string") != -1:
        # 字符串string.xml文件中的查找规则
        str_xml__pattern = re.compile('("\s*)(' + resource_name + ')([\s*"])')
        # 字符串java文件中的查找规则
        str_java_pattern = re.compile('([^\.]R\s*\.\s*string\s*\.\s*)(' + resource_name + ')([\s,);])')
        # 字符串layout文件中的查找规则
        str_layout_xml_pattern = re.compile('([\s\W]@\s*string\s*/\s*)(' + resource_name + ')([\s\W])')
        return str_xml__pattern, str_layout_xml_pattern, str_java_pattern
    elif file_path.find("attr") != -1:
        # attr 资源在attr.xml中的匹配规则
        attr_xml_pattern = re.compile('(name\s*=\s*"\s*)(' + resource_name + ')([\s\W"])')
        # attr 资源在layout文件中的查找规则
        attr_layout_pattern = re.compile('(?<!(android|[\s]{2}tools))(:\s*)(' + resource_name + ')(\s*=)')
        # attr 资源在java文件中的查找规则
        attr_java_pattern = re.compile(
            '([^\.]R\s*\.\s*styleable\s*\.\s*)(' + resource_name + ')([_\s,;)])|([^\.]R\s*\.\s*styleable\s*\.\s*\S*_)(' +
            resource_name + ')([\s,;)])')
        return attr_xml_pattern, attr_layout_pattern, attr_java_pattern
    elif file_path.find("color") != -1:
        # color资源在color.xml文件中匹配规则
        color_xml_pattern = re.compile('(name\s*=\s*"\s*)(' + resource_name + ')([\s"])')
        # color资源在layout文件中的匹配规则
        color_layout_pattern = re.compile('([\s\W]@\s*color\s*/\s*)(' + resource_name + ')([\s\W])')
        # color 资源在java文件中的匹配规则
        color_java_pattern = re.compile('([^\.]R\s*\.\s*color\s*\.\s*)(' + resource_name + ')([\s,);])')
        return color_xml_pattern, color_layout_pattern, color_java_pattern
    elif file_path.find("dimen") != -1:
        # dimen资源在dimen.xml中的匹配规则
        dimen_xml_pattern = re.compile('(name\s*=\s*"\s*)(' + resource_name + ')([\s"])')
        # dimen资源在layout文件中的匹配规则
        dimen_layout_pattern = re.compile('([\s\W]@\s*dimen\s*/\s*)(' + resource_name + ')([\s\W])')
        # dimen 资源在java文件中的匹配规则
        dimen_java_pattern = re.compile('([^\.]R\s*\.\s*dimen\s*\.\s*)(' + resource_name + ')([\s,);])')
        return dimen_xml_pattern, dimen_layout_pattern, dimen_java_pattern

    elif file_path.find("style") != -1:
        # style资源在style.xml中的匹配规则
        style_xml_pattern = re.compile('(style\s*name\s*=\s*"\s*)(' + resource_name + ')([\s"])')
        # style资源在layout文件中的匹配规则
        style_layout_pattern = re.compile('([\s\W]@\s*style\s*/\s*)(' + resource_name + ')([\s\W])')
        # style 资源在java文件中的匹配规则
        style_java_pattern = re.compile('([^\.]R\s*\.\s*style\s*\.\s*)(' + resource_name + ')([\s,);:])')
        return style_xml_pattern, style_layout_pattern, style_java_pattern
    else:
        return None, None, None


# 获取所有非文件资源名称
def get_not_file_resources(path):
    global IsFix, Prefix
    str_lists = []
    str_file = open(path, 'r')
    if IsFix:
        resource_pat = re.compile('name\s*=\s*"\s*' + Prefix + '([^\s]*)\s*"[\s>/]')
    else:
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


''''''''''''''''''''''''''''''''''''''''''''''以下是重命名文件资源方法'''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# 重命名文件资源方法
def rename_file():
    global LogFile, Prefix, NeedChangeModule
    res_path = get_module_path(NeedChangeModule) + "/src/main/res/"
    if not os.path.exists(res_path):
        print("{} doesn't exits!".format(res_path))
        return
    for file in os.listdir(res_path):
        file_path = res_path + file
        if file.find("value") != -1:
            # 跳过value相关文件夹
            continue
        if not os.path.isdir(file_path):
            # 非文件夹忽略
            continue
        else:
            rename_file_res_dir(file_path)


# 为某个资源文件夹下的资源文件重命名
def rename_file_res_dir(dir_path):
    global Prefix, IsFix
    # 遍历该资源文件夹
    for res_file in os.listdir(dir_path):
        file_path = dir_path + "/" + res_file
        if os.path.isdir(res_file):
            # 如果该资源文件夹下还有文件夹，忽略
            continue
        elif (not IsFix) and res_file.startswith(Prefix):
            continue
        else:
            if not IsFix:
                # 非修复模式下先将此文件本身加上前缀
                os.rename(file_path, dir_path + "/" + Prefix + res_file)
                log_string("rename res file: {} ----> {}".format(res_file, Prefix + res_file))

            if IsFix:
                # 取到tcl_listitem_test.xml中的listitem_test部分
                resource_name = res_file.split(".")[0].replace(Prefix, "")
            else:
                resource_name = res_file.split(".")[0]
            # databinding_pat 除非文件是layout文件，不然会是空
            xml_pat, java_pat, databinding_pat = get_file_pattern(file_path, resource_name)
            # 找到该资源上层的每一个模块，分别修改
            for mod in WorkModule:
                module_path = get_module_path(mod)
                log(res_file, mod, None)
                rename_file_dir(module_path, resource_name, os.path.basename(module_path), xml_pat, java_pat,databinding_pat)


def rename_file_dir(dir_path, resource_name, module_name, xml_pat, java_pat, databinding_pat):
    """
    重命名某个文件夹下某个文件资源的所有引用
    :param dir_path: 文件路径
    :param resource_name: 文件资源名称
    :param module_name:  模块名称
    :param xml_pat:  xml中的引用正则
    :param java_pat:  java文件中的引用正则
    :param databinding_pat:  java中databinding生成的正则，只对layout文件有效，其他情况下为空
    """
    global ExcludeDir
    for file in os.listdir(dir_path):
        file_path = dir_path + "/" + file
        if os.path.isdir(file_path) and file not in ExcludeDir:
            rename_file_dir(file_path, resource_name, module_name, xml_pat, java_pat, databinding_pat)
        elif not os.path.isdir(file_path):
            if file.endswith(".java") or file.endswith(".xml"):
                rename_file_file(file_path, resource_name, module_name, xml_pat, java_pat, databinding_pat)


def rename_file_file(file_path, resource_name, module_name, xml_pat, java_pat, databinding_pat):
    """
    为某个文件重命名所有对某个资源文件的引用
    :param file_path: 文件路径
    :param resource_name: 资源名称
    :param module_name: 模块名称
    :param xml_pat:  改文件资源在xml中的引用正则
    :param java_pat: 该文件资源在java文件中的引用正则
    :param databinding_pat:  layout文件资源在java中生成的databinding规则
    """
    global Prefix
    for line in fileinput.input(file_path, inplace=1):
        if file_path.endswith(".java"):
            # 对于java文件
            if line.lstrip().startswith("//") or line.lstrip().startswith("/*"):
                # 跳过注释行
                print(line, end="")
            elif java_pat.search(line) is None and (
                    databinding_pat is not None and databinding_pat.search(line) is None):
                # 跳过不包含目标的行
                print(line, end="")
            elif java_pat.search(line) is not None:
                # 修改正常的java对资源文件的引用
                line = java_pat.sub('\g<1>' + Prefix + resource_name + '\g<3>', line)
                print(line, end="")
                log(resource_name, module_name, os.path.basename(file_path))
            elif databinding_pat is not None and databinding_pat.search(line) is not None:
                # 修改databinding生成的类名引用
                new_name = get_databinding_name(Prefix+resource_name)
                line = databinding_pat.sub('\g<1>' + new_name + '\g<3>', line)
                print(line, end="")
                log(resource_name, module_name, os.path.basename(file_path))
            else:
                print(line, end="")
        elif file_path.endswith(".xml"):
            if line.lstrip().startswith("<!--"):
                # 跳过注释行
                print(line, end="")
            elif xml_pat.search(line) is None:
                # 跳过不包含目标的行
                print(line, end="")
            else:
                line = xml_pat.sub('\g<1>' + Prefix + resource_name + '\g<3>', line)
                print(line, end="")
                log(resource_name, module_name, os.path.basename(file_path))

    fileinput.close()


# 获取不同资源文件对应的正则表达式
def get_file_pattern(dir_path, file_name):
    """
    获取不同资源文件对应的正则表达式
    :param dir_path: 资源文件路径
    :param file_name: 文件名称
    :return:  返回三个值，分别是改资源文件在xml 和 java文件中的规则，如果是layout文件，则第三个值是databinding根据layout
              生成对象的规则，否则是none
    """
    if dir_path.find("drawable") != -1:
        # drawable下的资源在xml中的匹配规则
        drawable_xml_pattern = re.compile('([\s\W]@drawable\s*/)(' + file_name + ')([\s\W"<])')
        # drawable下的资源在java中的匹配规则
        drawable_java_pattern = re.compile('([^\.]R\s*\.\s*drawable\s*\.\s*)(' + file_name + ')([\s,);:])')
        return drawable_xml_pattern, drawable_java_pattern,None
    elif dir_path.find("mipmap") != -1:
        # mipmap下的资源在xml中的匹配规则
        mipmap_xml_pattern = re.compile('([\s\W]@mipmap\s*/)(' + file_name + ')([\s\W"<])')
        # mipmap下的资源在java中的匹配规则
        mipmap_java_pattern = re.compile('([^\.]R\s*\.\s*mipmap\s*\.\s*)(' + file_name + ')([\s,);:])')
        return mipmap_xml_pattern, mipmap_java_pattern,None
    elif dir_path.find("layout") != -1:
        # layout下的资源在xml中的匹配规则
        layout_xml_pattern = re.compile('([\s\W]@layout\s*/)(' + file_name + ')([\s\W"<])')
        # layout下的资源在java中的匹配规则
        layout_java_pattern = re.compile('([^\.]R\s*\.\s*layout\s*\.\s*)(' + file_name + ')([\s,);:])')
        # layout下的资源生成类的匹配规则
        databinding_pattern = re.compile('(.*)('+get_databinding_name(file_name)+')(.*)')
        return layout_xml_pattern, layout_java_pattern,databinding_pattern
    elif dir_path.find("anim") != -1:
        # anim下的资源在xml中的匹配规则
        anim_xml_pattern = re.compile('([\s\W]@anim\s*/)(' + file_name + ')([\s\W"<])')
        # anim下的资源在java中的匹配规则
        anim_java_pattern = re.compile('([^\.]R\s*\.\s*anim\s*\.\s*)(' + file_name + ')([\s,);:])')
        return anim_xml_pattern, anim_java_pattern,None
    elif dir_path.find("menu") != -1:
        # menu下的资源在xml中的匹配规则
        menu_xml_pattern = re.compile('([\s\W]@menu\s*/)(' + file_name + ')([\s\W"<])')
        # menu下的资源在java中的匹配规则
        menu_java_pattern = re.compile('([^\.]R\s*\.\s*menu\s*\.\s*)(' + file_name + ')([\s,);:])')
        return menu_xml_pattern, menu_java_pattern,None

    else:
        return None, None,None


def get_databinding_name(file_name: str) -> str:
    """
    根据xml文件名获取到databinding生成的对象名称,ru tdf_component_button.xml 得到TdfComponentButtonBinding
    :param file_name: xml文件名称
    :return: 处理后的名称
    """
    chs = list(file_name)
    chs[0] = chs[0].upper()
    for index in range(len(chs)):
        if chs[index] == "_" and index < len(chs) - 1:
            # 将一个字母大写
            chs[index + 1] = chs[index + 1].upper()

    res = ''.join(chs)
    return res.replace("_", "") + "Binding"


''''''''''''''''''''''''''''''''''''''''''''''以下是一些辅助方法'''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# 命令分发
def cmd():
    global Prefix, ExcludeDir, WorkModule, IsFix, NeedChangeModule
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hfp:e:m:t:",
                                   ["help", "fix", "prefix=", "exclude=", "module=", "target="])
        for o, a in opts:
            if o in ("-h", "--help"):
                help_info()
                sys.exit(0)
            elif o in ("-p", "--prefix"):
                Prefix = a
            elif o in ("-e", "--exclude"):
                dirs = a.replace(' ', '').split(",")
                ExcludeDir = ExcludeDir + dirs
            elif o in ("-m", "--module"):
                modules = a.replace(' ', '').split(",")
                WorkModule.extend(modules)
            elif o in ("-f", "--fix"):
                IsFix = True
            elif o in ("-t", "--target"):
                NeedChangeModule = a
                # 本身这个模块也要修改
                WorkModule.append(a)
            else:
                print("Wrong argument!")
                sys.exit(-1)

    except getopt.GetoptError:
        print("Wrong argument!")
        sys.exit(-1)


# 输出帮助信息
def help_info():
    str_help = """
     -m  <example1,example2>  传入本模块的上层依赖模块，有多个模块用“,”分割,不需要尖括号
     -p  <pre_examp>          指定前缀名称
     -e  <example1,example2>  指定排除的目录，虽然资源名称改了，但某些目录肯定不用有变动的，这里可以排除掉，
                              默认排除了：'build', '.idea', 'target', '.gradle', 'lib', '.git', 
                              'gradle', 'assets'
     -h                       打印帮助
     -f                       如果之前修改时遗漏了某个模块，利用 -p <pre_example> -m <遗漏的module>  -f
                              这三个参数可以将遗漏的模块中的资源重命名
    """
    print(str_help)


# 输出非文件资源的日志日志
def log(resource_name, module_name, file_name):
    global Prefix, LogFile
    if LogFile is None:
        return
    if resource_name and module_name and file_name:
        # 此处涉及到了向文件中写信息，不能有任何print相关
        log_str = "{}  :   {}    : {} -------> {}\n".format(module_name, file_name, resource_name,
                                                            Prefix + resource_name)
        LogFile.write(log_str)
    elif resource_name and module_name:
        log_str = "Start rename {} in {}\n".format(resource_name, module_name)
        sys.stdout.write(log_str)
        LogFile.write(log_str)
    elif resource_name:
        log_str = "Start rename {} \n".format(resource_name)
        sys.stdout.write(log_str)
        LogFile.write(log_str)


# 向日志中写入一句话
def log_string(string):
    global LogFile
    if LogFile is None:
        return
    print(string)
    LogFile.write(string + "\n")


# 初始化输出日志
def init():
    global LogFile, IsFix, AllModulePath, RootDir
    RootDir = os.path.abspath(os.path.curdir)
    AllModulePath = get_all_module_path(RootDir)
    path = os.path.join(os.environ['HOME'], "prefixLog_" + os.path.basename(os.path.abspath(os.curdir)) + ".txt")
    if IsFix:
        LogFile = open(path, 'a')
    else:
        LogFile = open(path, 'w')


# 一些简单的检查
def check():
    global Prefix, WorkModule
    if not Prefix:
        print("Please add -p argument")
        sys.exit(-1)
    if len(WorkModule) == 0:
        print("Please add -m argument")
        sys.exit(-1)


def main():
    cmd()
    init()
    check()
    rename_not_file()
    rename_file()
    return


def test():
    content = """
     android:text="@string/jaogn"
  tools:text="@string/jfaong"
app:text="@string/jtgoang"
    """
    regx = "(?<!(android|[\s]{2}tools))(:\s*)(text)(\s*=)"
    p = re.compile(regx)
    print(p.search(content))
    res = p.sub("\g<1>\g<2>hehe\g<4>",content)
    print(res)



try:
    main()
    # test()

# 以下是测试使用

except KeyboardInterrupt:
    pass
