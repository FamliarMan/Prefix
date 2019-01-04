# Android资源批量添加前缀
## 使用限制
1. 修改某个模块资源时，必须自己传入依赖了该模块的上层模块，也就是必须自己做依赖分析。
2. 修改某个模块资源时，传入的该模块的上层模块目录必须和该模块是同级或上一级的
3. 个别情况下会出现小错误，但编译时会发现，不用担心
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
## 使用方法
在要修改的模块的根目录(无论是修改app还是library1还是library2)执行下列命令：
python3 prefix.py  -m app,library1  -p lib2_    -e hehe,test
**注意：绝对不要包含任何空格**

参数说明：
* -m  传入本模块的上层依赖模块，有多个模块用“,”分割
* -p  指定前缀名称
* -e  指定排除的目录，虽然资源名称改了，但某些目录肯定不用有变动的，这里可以排除掉，默认排除了：'build', '.idea', 'target', '.gradle', 'lib', '.git', 'gradle', 'assets'
*  -f 如果之前使用-m指定依赖的上层模块时，命令执行完发现漏了模块，可以重新利用-m指定遗漏的模块，只不过要加上-f参数
* -h 打印帮助

## 不足
由于项目开发过程不够规范，很可能出现同名资源，而且同名资源不一定相同，那么在批量替换时可能会将一个同名的其他资源替换另一个同名的资源，
所以我们可以在替换之前先把这些同名资源全部找出来：
直接在项目根目录下执行：
```
python3 repeat.py
```
重名情况会以json格式输出在控制台