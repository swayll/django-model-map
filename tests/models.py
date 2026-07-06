from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class User(models.Model):
    username = models.CharField(max_length=50)


class Author(models.Model):
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)


class Tag(models.Model):
    title = models.CharField(max_length=50)


class Post(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()


class SoloModel(models.Model):
    name = models.CharField(max_length=50)


class HiddenPost(models.Model):
    post = models.ForeignKey(Post, related_name='+', on_delete=models.CASCADE)


class Article(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
