# Android资源批量添加前缀
## 使用限制
1. 修改某个模块资源时，必须自己传入依赖了该模块的上层模块，也就是必须自己做依赖分析。
2. 修改某个模块资源时，传入的该模块的上层模块目录必须和该模块是同级或上一级的
```
.
├── app
│   ├── app.iml
│   ├── build
│   ├── build.gradle
│   ├── libs
│   ├── proguard-rules.pro
│   └── src
├── build
│   └── android-profile
├── build.gradle
├── gradle
│   └── wrapper
├── gradle.properties
├── gradlew
├── gradlew.bat
├── library1
│   ├── build
│   ├── build.gradle
│   ├── library1.iml
│   ├── libs
│   ├── proguard-rules.pro
│   ├── sampledata
│   └── src
├── library2
│   ├── build
│   ├── build.gradle
│   ├── library2.iml
│   ├── libs
│   ├── proguard-rules.pro
│   └── src
├── local.properties
├── PrefixTest.iml
└── settings.gradle

``` 
以上面这个工程为例，依赖关系时app ------>  library1 ------- >library2
app是最顶层的，如果要修改library1模块的资源，那么最好保证app和library1平级或者在library1上一级目录。
## 使用方法
在要修改的模块的根目录执行下列命令：
python3 prefix.py  -m [app|library1]  -p lib2_    -e [hehe|test]

参数说明：
* -m  传入本模块的上层依赖模块，有过个模块用“|”分割，注意，不需要示例中的中括号
* -p  指定前缀名称
-e  指定排除的目录，虽然资源名称改了，但某些目录肯定不用有变动的，这里可以排除掉，默认排除了：'build', '.idea', 'target', '.gradle', 'lib', '.git', 'gradle', 'assets'
-h 打印帮助