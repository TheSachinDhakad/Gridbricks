from rest_framework import serializers


class ForecastRowSerializer(serializers.Serializer):
    startTime = serializers.DateTimeField()
    forecastPublishTime = serializers.DateTimeField(allow_null=True)
    forecastGeneration = serializers.FloatField(allow_null=True)
    actualGeneration = serializers.FloatField()
    errorMW = serializers.FloatField(allow_null=True)
    absoluteErrorMW = serializers.FloatField(allow_null=True)


class AccuracyMetricsSerializer(serializers.Serializer):
    maeMW = serializers.FloatField(allow_null=True)
    rmseMW = serializers.FloatField(allow_null=True)
    meanBiasErrorMW = serializers.FloatField(allow_null=True)
    maePercentOfMeanActual = serializers.FloatField(allow_null=True)