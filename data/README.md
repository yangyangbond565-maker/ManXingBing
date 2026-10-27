# 数据目录说明

data/ 下的大文件不进入源代码压缩包，可用脚本重新生成：

- data/generated/：7 个 CSV + manifest.json（固定 seed）。
- data/warehouse/ods/：7 个 TSV + ods_local.sql（Spark 本地输入）。
- data/sync/：MySQL 导出的原始 TSV。
- data/ads/：可选 ADS CSV 导出。
- data/test_generated/：pytest 生成的小样本。

重新生成：

~~~powershell
$env:PYTHONPATH="$PWD\python;$PWD\python\vendor"
$env:CHRONIC_DB_PASSWORD="***"
python -m chronic_disease.generate --patients 100000 --seed 20261020
python -m chronic_disease.load_mysql --truncate
python -m chronic_disease.sync_mysql_to_hive --mode local
~~~

数据全部为虚构数据，不对应真实个人。
