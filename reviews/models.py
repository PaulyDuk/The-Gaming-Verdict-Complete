
from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from developer.models import Developer
from publisher.models import Publisher
# Create your models here.


class Review(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    publisher = models.ForeignKey(
        Publisher, on_delete=models.CASCADE, related_name='reviews')
    developer = models.ForeignKey(
        Developer, on_delete=models.CASCADE, related_name='games')
    description = models.TextField()
    genres = models.ManyToManyField(
        'Genre', related_name='reviews', blank=True
    )
    release_date = models.DateField()

    # Review fields
    review_score = models.DecimalField(
        max_digits=3, decimal_places=1, blank=True, null=True)  # 0.0 to 10.0
    review_text = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    review_date = models.DateTimeField(blank=True, null=True)

    # Media
    featured_image = CloudinaryField('image', default='placeholder')

    # Metadata
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    # User engagement
    likes = models.ManyToManyField(User, related_name='game_likes', blank=True)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Game'
        verbose_name_plural = 'Games'

    def __str__(self):
        if self.review_score is not None:
            score_display = f"{self.review_score}/10"
        else:
            score_display = "No Score"
        return f"{self.title} | Score: {score_display}"

    def number_of_likes(self):
        return self.likes.count()


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def games_count(self):
        """Return the number of reviews (games) associated with this genre"""
        return self.reviews.count()


class UserComment(models.Model):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="user_comments")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_commenter")
    body = models.TextField()
    approved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_on"]
        verbose_name = 'User Comment'
        verbose_name_plural = 'User Comments'

    def __str__(self):
        review_title = self.review.title if self.review else "Unknown Review"
        return f"Comment by {self.author} on {review_title}"


class UserReview(models.Model):
    game = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='user_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 11)])  # 1-10 rating
    review_text = models.TextField()
    approved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    helpful_votes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('game', 'user')  # One review per user per game
        verbose_name = 'User Review'
        verbose_name_plural = 'User Reviews'

    def __str__(self):
        return f"{self.user.username}'s review of {self.game.title}"
