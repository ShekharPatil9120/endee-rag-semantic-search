from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_page, name='chat_page'),        # /chat/
    path('ragbot/', views.rag_chatbot, name='rag_chatbot'),  # /chat/ragbot/
]
