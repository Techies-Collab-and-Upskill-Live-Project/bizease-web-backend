from rest_framework import generics, permissions, status
from .models import Report
from .serializers import ReportSerializer
from django_filters import rest_framework as filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse

class ReportListCreateView(generics.ListCreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Report.objects.filter(created_by=self.request.user)
    
class ReportFilter(filters.FilterSet):
    class Meta:
        model = Report
        fields = {
            'report_type': ['exact'],
            'created_at' : ['exact', 'gte', 'lte']
        }

class ReportListView(generics.ListCreateAPIView):
    ...
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ReportFilter

class ReportDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        report = Report.objects.get(pk=pk, created_by=request.user)
        if not report.file:
            return Response({"error: File not found",}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(report.file.open(), as__attachment==True)