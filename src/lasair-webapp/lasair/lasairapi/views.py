from django.shortcuts import get_object_or_404, render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import ConeSerializer, StreamlogSerializer, QuerySerializer 
from .serializers import LightcurvesSerializer, SherlockQuerySerializer, SherlockObjectSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .query_auth import QueryAuthentication

class ConeView(APIView):
    authentication_classes = [TokenAuthentication, QueryAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        #events = Events.objects.all()
        #serializer = EventSerializer(events, many=True)
        return Response({"Error": "GET is not implemented for this service."})

    def post(self, request, format=None):
        serializer = ConeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save()
            return Response(message, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StreamlogView(APIView):
    authentication_classes = [TokenAuthentication, QueryAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"Error": "GET is not implemented for this service."})

    def post(self, request, format=None):
        serializer = StreamlogSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save()
            return Response(message, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QueryView(APIView):
    authentication_classes = [TokenAuthentication, QueryAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"Error": "GET is not implemented for this service."})

    def post(self, request, format=None):
        serializer = QuerySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save()
            return Response(message, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LightcurvesView(APIView):
    authentication_classes = [TokenAuthentication, QueryAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"Error": "GET is not implemented for this service."})

    def post(self, request, format=None):
        serializer = LightcurvesSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save()
            return Response(message, status=status.HTTP_200_OK)

class SherlockQueryView(APIView):
    authentication_classes = [TokenAuthentication, QueryAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"Error": "GET is not implemented for this service."})

    def post(self, request, format=None):
        serializer = SherlockQuerySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save()
            return Response(message, status=status.HTTP_200_OK)

class SherlockObjectView(APIView):
    authentication_classes = [TokenAuthentication, QueryAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"Error": "GET is not implemented for this service."})

    def post(self, request, format=None):
        serializer = SherlockObjectSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save()
            return Response(message, status=status.HTTP_200_OK)
