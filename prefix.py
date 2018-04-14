#!/usr/bin/python3
# coding=utf-8
# -*- coding：utf-8 -*-
import sys, getopt, re
import os, fileinput

# 排除的目录
ExcludeDir = ['build', '.idea', 'target', '.gradle', 'lib', '.git', 'gradle', 'assets']

# 需要处理的模块
WorkModule = []

# 需要添加的前缀
Prefix = ""

# 输出日志
LogFile = None


#################################### 以下是非文件资源的重命名方法 ####################################################

# 重命名非文件资源
def rename_not_file():
    global LogFile, Prefix
    possible_path = ["strings.xml", "string.xml","colors.xml","color.xml","attr.xml",
                     "attrs.xml","style.xml","styles.xml","dimen.xml","dimens.xml"]
    has_resource_file = False
    for path in possible_path:
        resource_file_path = os.path.abspath(".") + '/src/main/res/values/' + path
        if not os.path.exists(resource_file_path):
            continue
        has_resource_file = True
        # 获取所有要修改的字符的名称
        str_resources = get_not_file_resources(resource_file_path)
        for s in str_resources:
            if s.startswith(Prefix):
                continue
            log( s, None, None)
            # 找到该资源上层的每一个模块，分别修改
            for module in WorkModule:
                module_path = os.path.abspath("..") + "/" + module
                if not os.path.exists(module_path):
                    # 继续向上一层寻找
                    module_path = os.path.abspath("../..") + "/" + module
                    if not os.path.exists(module_path):
                        continue
                log(s, module, None)
                xml_pat,layout_pat,java_pat = get_not_file_pattern(resource_file_path, s)
                rename_not_file_dir(module_path, s, module,xml_pat,layout_pat,java_pat)

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
                rename_not_file_file(cur_path, resource_name, module_name,xml_pat,layout_pat,java_pat)


# 修改某个文件的非文件串资源名称
def rename_not_file_file(file_path, resource_name, module_name,xml_pat,layout_pat,java_pat):
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
                log(LogFile, resource_name, module_name, os.path.basename(file_path))

        elif file_path.endswith(".xml"):
            if (file_path.find("src/main/res/values") != -1):
                # 该xml文件是非layout,drawable文件,一般是string.xml,color.xml等文件
                if line.find("<!--") != -1:
                    # 跳过注释行
                    print(line, end="")
                    continue
                elif xml_pat.search(line) is None:
                    # 跳过不包含目标的行
                    print(line, end="")
                else:
                    line =xml_pat.sub('\g<1>' + Prefix + resource_name + '\g<3>', line)
                    print(line, end="")
                    log(LogFile, resource_name, module_name, os.path.basename(file_path))
            else:
                # 对于layout和drawable中的xml文件
                if line.find("<!--") != -1:
                    # 跳过注释行
                    print(line, end="")
                elif layout_pat.search(line) is None:
                    # 跳过不包含目标的行
                    print(line, end="")
                else:
                    line = layout_pat.sub('\g<1>' + Prefix + resource_name + '\g<3>', line)
                    print(line, end="")
                    log(LogFile, resource_name, module_name, os.path.basename(file_path))

    fileinput.close()


# 获取非文件资源的正则匹配规则
def get_not_file_pattern(file_path, resource_name):
    if file_path.find("string") != -1:
        # 字符串string.xml文件中的查找规则
        str_xml__pattern = re.compile('("\s*)(' + resource_name + ')([\s*"])')
        # 字符串java文件中的查找规则
        str_java_pattern = re.compile('(R\s*\.\s*string\s*\.\s*)(' + resource_name + ')([\s,);])')
        # 字符串layout文件中的查找规则
        str_layout_xml_pattern = re.compile('("\s*@\s*string\s*/\s*)(' + resource_name + ')([\s"])')
        return str_xml__pattern, str_layout_xml_pattern, str_java_pattern
    elif file_path.find("attr") != -1:
        # attr 资源在attr.xml中的匹配规则
        attr_xml_pattern = re.compile('(name\s*=\s*"\s*)(' + resource_name + ')([\s*"])')
        # attr 资源在layout文件中的查找规则
        attr_layout_pattern = re.compile('(:\s*)(' + resource_name + ')(\s*=)')
        # attr 资源在java文件中的查找规则
        attr_java_pattern = re.compile('(R\s*\.\s*styleable\s*\.\s*)('+resource_name+')([_\s,;)])|(R\s*\.\s*styleable\s*\.\S*_)('+resource_name+')([\s,;)])')
        return attr_xml_pattern, attr_layout_pattern, attr_java_pattern
    elif file_path.find("color") != -1:
        # color资源在color.xml文件中匹配规则
        color_xml_pattern = re.compile('(name\s*=\s*"\s*)(' + resource_name + ')([\s"])')
        # color资源在layout文件中的匹配规则
        color_layout_pattern = re.compile('("\s*@\s*color\s*/\s*)(' + resource_name + ')([\s"])')
        # color 资源在java文件中的匹配规则
        color_java_pattern = re.compile('(R\s*\.\s*color\s*\.\s*)(' + resource_name + ')([\s,);])')
        return color_xml_pattern,color_layout_pattern,color_java_pattern
    elif file_path.find("dimen") != -1:
        # dimen资源在dimen.xml中的匹配规则
        dimen_xml_pattern = re.compile('(name\s*=\s*"\s*)(' + resource_name + ')([\s"])')
        # dimen资源在layout文件中的匹配规则
        dimen_layout_pattern = re.compile('("\s*@\s*dimen\s*/\s*)(' + resource_name + ')([\s"])')
        # dimen 资源在java文件中的匹配规则
        dimen_java_pattern = re.compile('(R\s*\.\s*dimen\s*\.\s*)(' + resource_name + ')([\s,);])')
        return dimen_xml_pattern,dimen_layout_pattern,dimen_java_pattern

    elif file_path.find("style") != -1:
        # style资源在style.xml中的匹配规则
        style_xml_pattern = re.compile('(style\s*name\s*=\s*"\s*)(' + resource_name + ')([\s"])')
        # style资源在layout文件中的匹配规则
        style_layout_pattern = re.compile('("\s*@\s*style\s*/\s*)(' + resource_name + ')([\s"])')
        # style 资源在java文件中的匹配规则
        style_java_pattern = re.compile('(R\s*\.\s*style\s*\.\s*)(' + resource_name + ')([\s,);])')
        return style_xml_pattern,style_layout_pattern,style_java_pattern
    else:
        return None,None,None


# 获取所有非文件资源名称
def get_not_file_resources(path):
    str_lists = []
    str_file = open(path, 'r')
    resourcePat = re.compile('name\s*=\s*"([^\s]*)\s*"[\s>/]')
    for line in str_file:
        if line.find("<item") != -1:
            continue
        if line.startswith('<!--'):
            continue
        res = resourcePat.findall(line)
        if len(res) != 0:
            str_lists.extend(res)
    return str_lists


# 重命名文件资源方法
def rename_file():
    global LogFile, Prefix
    res_path = os.path.abspath(os.curdir)+"/src/main/res/"
    if not os.path.exists(res_path):
        print("{} doesn't exits!".format(res_path))
        return
    for file in os.listdir(res_path):
        file_path = res_path+"/"+file
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
    global Prefix
    # 遍历该资源文件夹
    for res_file in os.listdir(dir_path):
        file_path = dir_path+"/"+res_file
        if os.path.isdir(res_file):
            # 如果该资源文件夹下还有文件夹，忽略
            continue
        elif res_file.startswith(Prefix):
            continue
        else:
            #先将此文件本身加上前缀
            os.rename(file_path,dir_path+"/"+Prefix+res_file)
            log_string("rename res file: {} ----> {}".format(res_file,Prefix+res_file))
            xml_pat,java_pat = get_file_pattern(file_path,res_file)
            # 找到该资源上层的每一个模块，分别修改
            for module in WorkModule:
                module_path = os.path.abspath("..") + "/" + module
                if not os.path.exists(module_path):
                    # 继续向上一层寻找
                    module_path = os.path.abspath("../..") + "/" + module
                    if not os.path.exists(module_path):
                        continue
                log(res_file, module, None)
                rename_file_dir(module_path,res_file,os.path.basename(module_path),xml_pat,java_pat)


# 为某个文件夹重命名文件资源
def rename_file_dir(dir_path,resource_name,module_name,xml_pat,java_pat):
    global ExcludeDir
    for file in os.listdir(dir_path):
        file_path = dir_path+"/"+file
        if os.path.isdir(file_path) and file not in ExcludeDir:
            rename_file_dir(file_path,module_name,xml_pat,java_pat)
        elif not os.path.isdir(file_path) :
            if file.endswith(".java") or file.endswith(".xml"):
                rename_file_file(file_path,resource_name,module_name,xml_pat,java_pat)


def rename_file_file(file_path,resource_name,module_name,xml_pat,java_pat):
    global Prefix
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
                line = java_pat.sub('\g<1>' + Prefix + resource_name + '\g<3>', line)
                print(line, end="")
                log(resource_name, module_name, os.path.basename(file_path))
        elif file_path.endswith(".xml"):
            if line.find("<!--") != -1:
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
def get_file_pattern(dir_path,file_name):
    if dir_path.find("drawable") != -1:
        #drawable下的资源在xml中的匹配规则
        drawable_xml_pattern = re.compile('(@drawable\s*/)('+file_name+')([\s"])')
        #drawable下的资源在java中的匹配规则
        drawable_java_pattern = re.compile('(R\s*\.\s*drawable\s*\.\s*)(' + file_name+ ')([\s,);])')
        return drawable_xml_pattern,drawable_java_pattern
    elif dir_path.find("mipmap") != -1:
        #mipmap下的资源在xml中的匹配规则
        mipmap_xml_pattern = re.compile('(@mipmap\s*/)('+file_name+')([\s"])')
        #mipmap下的资源在java中的匹配规则
        mipmap_java_pattern = re.compile('(R\s*\.\s*mipmap\s*\.\s*)(' + file_name+ ')([\s,);])')
        return mipmap_xml_pattern,mipmap_java_pattern
    elif dir_path.find("layout") != -1:
        #layout下的资源在xml中的匹配规则
        layout_xml_pattern = re.compile('(@layout\s*/)('+file_name+')([\s"])')
        #layout下的资源在java中的匹配规则
        layout_java_pattern = re.compile('(R\s*\.\s*layout\s*\.\s*)(' + file_name+ ')([\s,);])')
        return layout_xml_pattern,layout_java_pattern
    elif dir_path.find("anim") != -1:
        #anim下的资源在xml中的匹配规则
        anim_xml_pattern = re.compile('(@anim\s*/)('+file_name+')([\s"])')
        #anim下的资源在java中的匹配规则
        anim_java_pattern = re.compile('(R\s*\.\s*anim\s*\.\s*)(' + file_name+ ')([\s,);])')
        return anim_xml_pattern,anim_java_pattern
    elif dir_path.find("menu") != -1:
        #menu下的资源在xml中的匹配规则
        menu_xml_pattern = re.compile('(@menu\s*/)('+file_name+')([\s"])')
        #menu下的资源在java中的匹配规则
        menu_java_pattern = re.compile('(R\s*\.\s*menu\s*\.\s*)(' + file_name+ ')([\s,);])')

    else:
        return None,None




############################## 以下一些辅助方法 #############################################


# 命令分发
def cmd():
    global Prefix, ExcludeDir, WorkModule
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hp:e:m:", ["help", "prefix=", "exclude=", "module="])
        for o, a in opts:
            if o in ("-h", "--help"):
                help()
            elif o in ("-p", "--prefix"):
                Prefix = a
            elif o in ("-e", "--exclude"):
                dirs = a.split("|")
                ExcludeDir = ExcludeDir + dirs
            elif o in ("-m", "--module"):
                modules = a.split("|")
                WorkModule.extend(modules)
            else:
                print("Wrong argument!")

    except getopt.GetoptError:
        print("Wrong argument!")


# 输出帮助信息
def help():
    return

# 输出非文件资源的日志日志
def log(resource_name, module_name, file_name):
    global Prefix,LogFile
    if LogFile is None:
        return
    if resource_name and module_name and file_name:
        # 此处涉及到了向文件中写信息，不能有任何print相关
        log = "{}  :   {}    : {} -------> {}\n".format(module_name, file_name, resource_name, Prefix + resource_name)
        LogFile.write(log)
    elif resource_name and module_name:
        log = "Start rename {} in {}\n".format(resource_name, module_name)
        sys.stdout.write(log)
        LogFile.write(log)
    elif resource_name:
        log = "Start rename {} \n".format(resource_name)
        sys.stdout.write(log)
        LogFile.write(log)
# 向日志中写入一句话
def log_string(string):
    global LogFile
    print(string)
    LogFile.write(string)


# 初始化输出日志
def init():
    global LogFile
    path = os.path.join(os.environ['HOME'], "prefixLog_" + os.path.basename(os.path.abspath(os.curdir)) + ".txt")
    LogFile = open(path, 'w')
    WorkModule.append(os.path.basename(os.path.abspath(os.path.curdir)))


def main():
    global LogFile
    init()
    cmd()
    # rename_not_file()
    rename_file()
    return


try:
    main()
except KeyboardInterrupt:
    pass
