from pyspark.sql import SparkSession
spark = (SparkSession.builder.appName("hdfs-smoke").master("local[2]")
         .config("spark.ui.enabled", "false").getOrCreate())
spark.sparkContext.setLogLevel("WARN")
path = "hdfs://192.168.20.135:9000/warehouse/chronic_disease/ods/patient_info/data.tsv"
df = spark.read.option("sep", "\t").option("header", "false").schema(
    "patient_id int, gender string, age int, province string, city string, id_number string, phone string, create_time string"
).csv(path)
print("HDFS_ROW_COUNT", df.count())
print("HDFS_FIRST", df.select("patient_id", "gender", "age", "province").first())
spark.stop()
