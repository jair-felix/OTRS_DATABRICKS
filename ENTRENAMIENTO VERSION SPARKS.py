# -*- coding: utf-8 -*-
"""VERSION

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17CB9jUoeO9G5XS1GcS2eJT_4FTXe0A2-
"""

!pip install pyspark
!pip install findspark
!pip install pyhive

import findspark
findspark.init()

import pandas as pd
import pyspark

from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

"""INGRESAR CSV"""

from google.colab import files
uploaded = files.upload()

#df = spark.createDataFrame(pd.read_csv(next(iter(uploaded.keys())), sep="|", encoding="ISO-8859-1"))
#df.show()

df = spark.read.option("delimiter", ";").csv(next(iter(uploaded.keys())), header=True, inferSchema=True)
df.show()

"""HACER UN DATAFRAME CON COLUMNAS"""

# Carga los datos en un DataFrame y asigna nombres de columna
column_names = ["DEL AREA", "TIPO", "TITULO", "TEXTO"]
df = spark.read.option("delimiter", ";").csv(next(iter(uploaded.keys())), header=False, inferSchema=True).toDF(*column_names)

# Muestra el DataFrame con los nombres de columna
df.show()

"""Preprocesamiento de datos"""

from pyspark.sql.functions import udf, col, lower
from pyspark.ml.feature import Tokenizer
from pyspark.sql.types import StringType
import re

# Crea un Tokenizer para la columna "TEXTO"
tokenizer = Tokenizer(inputCol="TEXTO", outputCol="palabras")

# Aplica la tokenización al DataFrame
df_tokenized = tokenizer.transform(df)

# Define una función UDF para unir la lista de palabras en una cadena
def join_tokens(words):
    return " ".join(words)

join_tokens_udf = udf(join_tokens, StringType())

# Aplica la función UDF para unir las palabras en la columna "palabras"
df_cleaned = df_tokenized.withColumn("texto_limpio", join_tokens_udf(col("palabras")))

# Define una función UDF para eliminar la puntuación y caracteres especiales
def remove_punctuation(text):
    return re.sub(r'[^\w\s]', '', text)

remove_punctuation_udf = udf(remove_punctuation, StringType())

# Aplica la función UDF para eliminar puntuación y caracteres especiales en la columna "texto_limpio"
df_preprocessed = df_cleaned.withColumn("texto_limpio", remove_punctuation_udf(col("texto_limpio")))

# Convierte todas las palabras a minúsculas en la columna "texto_limpio"
df_preprocessed = df_preprocessed.withColumn("texto_lower", lower(col("texto_limpio")))

# Muestra el DataFrame preprocesado
df_preprocessed.show(truncate=False)

"""Creación de etiquetas y características"""

from pyspark.ml.feature import HashingTF, IDF, Tokenizer
from pyspark.ml.feature import StringIndexer
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline

# Tokenización de la columna de texto
tokenizer = Tokenizer(inputCol="TEXTO", outputCol="palabras")
df_tokenized = tokenizer.transform(df)

# Cálculo de TF (frecuencia de término)
hashingTF = HashingTF(inputCol="palabras", outputCol="rawFeatures")
df_tf = hashingTF.transform(df_tokenized)

# Cálculo de IDF (frecuencia inversa de documento)
idf = IDF(inputCol="rawFeatures", outputCol="features")
idfModel = idf.fit(df_tf)
df_features = idfModel.transform(df_tf)

# Creación de etiquetas numéricas para la columna "DEL AREA"
label_indexer = StringIndexer(inputCol="DEL AREA", outputCol="etiqueta_indexada")
df_indexed = label_indexer.fit(df_features).transform(df_features)

# División de datos en conjuntos de entrenamiento y prueba
train_data, test_data = df_indexed.randomSplit([0.8, 0.2], seed=123)

# Entrenamiento del modelo RandomForest
rf = RandomForestClassifier(labelCol="etiqueta_indexada", featuresCol="features", numTrees=100)
model = rf.fit(train_data)

# Predicción en el conjunto de prueba
predictions = model.transform(test_data)

# Mostrar las predicciones
predictions.select("TEXTO", "DEL AREA", "etiqueta_indexada", "prediction").show(truncate=False)

df_features.printSchema()

from pyspark.sql.functions import col

# Renombra la columna "DEL AREA" a "etiqueta"
df = df.withColumnRenamed("DEL AREA", "etiqueta")

from pyspark.ml.feature import HashingTF, IDF, Tokenizer

# Tokenización de la columna de texto
tokenizer = Tokenizer(inputCol="TEXTO", outputCol="palabras")
df_tokenized = tokenizer.transform(df)

# Cálculo de TF (frecuencia de término)
hashingTF = HashingTF(inputCol="palabras", outputCol="rawFeatures")
df_tf = hashingTF.transform(df_tokenized)

# Cálculo de IDF (frecuencia inversa de documento)
idf = IDF(inputCol="rawFeatures", outputCol="features")
idfModel = idf.fit(df_tf)
df_features = idfModel.transform(df_tf)

df_features.printSchema()

from pyspark.ml.feature import HashingTF, IDF, Tokenizer
from pyspark.ml.feature import StringIndexer
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline

# Tokenización de la columna de texto
tokenizer = Tokenizer(inputCol="TEXTO", outputCol="palabras")
df_tokenized = tokenizer.transform(df)

# Cálculo de TF (frecuencia de término)
hashingTF = HashingTF(inputCol="palabras", outputCol="rawFeatures")
df_tf = hashingTF.transform(df_tokenized)

# Cálculo de IDF (frecuencia inversa de documento)
idf = IDF(inputCol="rawFeatures", outputCol="features")
idfModel = idf.fit(df_tf)
df_features = idfModel.transform(df_tf)

# Creación de etiquetas numéricas para la columna "DEL AREA"
label_indexer = StringIndexer(inputCol="etiqueta", outputCol="etiqueta_indexada")
df_indexed = label_indexer.fit(df_features).transform(df_features)

# Entrenamiento del modelo RandomForest
rf = RandomForestClassifier(labelCol="etiqueta_indexada", featuresCol="features", numTrees=100)
model = rf.fit(df_indexed)

# Ahora puedes hacer predicciones en nuevos datos usando el modelo entrenado
# Por ejemplo, si tienes un DataFrame "nuevos_datos" con la columna "TEXTO"
# tokenizada y transformada de la misma manera que "df_tokenized", puedes hacer lo siguiente:
# predictions = model.transform(nuevos_datos)

from pyspark.ml.feature import HashingTF, IDF, Tokenizer, StringIndexer
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# ... (código anterior de tokenización, cálculo de TF-IDF y creación de etiquetas numéricas)

# Creación de etiquetas numéricas
indexer = StringIndexer(inputCol="etiqueta", outputCol="etiqueta_indexada")
df_indexed = indexer.fit(df_features).transform(df_features)

# División de datos en conjuntos de entrenamiento y prueba
train_data, test_data = df_indexed.randomSplit([0.8, 0.2], seed=123)

# Entrenamiento del modelo RandomForest
rf = RandomForestClassifier(labelCol="etiqueta_indexada", featuresCol="features", numTrees=100)
model = rf.fit(train_data)

# Predicción en el conjunto de prueba
predictions = model.transform(test_data)

# Evaluación del modelo
evaluator = MulticlassClassificationEvaluator(labelCol="etiqueta_indexada", predictionCol="prediction", metricName="accuracy")
accuracy = evaluator.evaluate(predictions)
print("Accuracy:", accuracy)
