from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView 
from rest_framework.views import APIView

# from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserSerializer, UserSignupSerializer, UserSigninSerializer
from rest_framework.permissions import AllowAny


# class SignupView(GenericAPIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = UserSignupSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             # refresh = RefreshToken.for_user(user)
#             return Response(
#                 {
#                     "user": serializer.data,
#                     # 'refresh': str(refresh),
#                     # 'access': str(refresh.access_token),
#                 },
#                 status=status.HTTP_201_CREATED,
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class SigninView(GenericAPIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = UserSigninSerializer(
#             data=request.data, context={"request": request}
#         )
#         if serializer.is_valid(raise_exception=True):
#             validated_data = getattr(serializer, "validated_data", {}) or {}
#             user = validated_data.get("user")
#             if user is None:
#                 return Response(
#                     {"detail": "Authentication failed"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#             user_serializer = UserSignupSerializer(user, context={"request": request})
#             return Response(user_serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]