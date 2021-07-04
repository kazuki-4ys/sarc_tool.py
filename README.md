# sarc_tool.py
3DS, WiiU, Switchで使用されているSARC,SZS(SARCをYaz0で圧縮したもの)を作成、展開するPythonスクリプトです。
バイトオーダー、SFNTにファイル名を書き込むかどうか、ファイルのアラインメントを指定してSARCを作成することができます。
SFNTにファイル名が書き込まれていないSARCを展開する場合は`HashTable.saht`からファイル名を取得します。
このスクリプトを使用するには`libyaz0`のインストールが必要です。
* `py -m pip install libyaz0`

## 使用方法:
 * `sarc_tool.py [Command] file/folder [Option...] outputfile/outputfolder`


## コマンド一覧:
|コマンド|説明|
| ---- | ---- |
|`x`|SARCを展開します|
|`c`|フォルダーからSARCを作成します|

## オプション一覧:
|オプション|説明|
| ---- | ---- |
|`--byteorder` or `-bo`|バイトオーダーを指定してSARCを作成します。使用できる値は`LE` or `BE`です。デフォルトは`LE`です。WiiUで使用する場合は`BE`に指定してください。|
|`--emptysfnt`|値を`TRUE`に設定するとSFNTにファイル名を書き込まずにSARCを作成します。代わりにファイル名とハッシュ値が書き込まれた`HashTable.saht`がSARCに追加されます。|
|`--alignment`|ファイルのアラインメントを指定します。デフォルトは`0x100`です。|
|`--compression` or `-c`|SARCを作成する際の圧縮形式を指定します。使用できる値は`yaz0`, `yaz1` or `none`です。指定しなかった場合はファイル名から自動で判断されます。|

## 具体例:
 * `sarc_tool.py x Gctr_ToadCircuit.szs Gctr_ToadCircuit.d`
 * `sarc_tool.py c Gctr_ToadCircuit.d -bo LE --alignment 0x80 Gctr_ToadCircuit.szs`