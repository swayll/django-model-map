from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)

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
