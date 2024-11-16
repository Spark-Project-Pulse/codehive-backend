import uuid
from django.db import models, connection
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex

# Things to note:
# 1. when using ForeignKey rels, Django's ORM automatically appends _id to the end of the field name (e.g. expert -> expert_id) in supabase
#   (you should NOT include _id manually at the end of any ForeignKey names)

# 2. however, when using PrimaryKeys (e.g. answer_id), you SHOULD include _id at the end of the field name (this is the standard in Django)

# 2. make sure you ONLY make changes to the database schema by editing this file (not the supabase dashboard), then push those changes using:
#    python manage.py makemigrations
#    python manage.py migrate

class Answers(models.Model):
    answer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expert = models.ForeignKey('Users', on_delete=models.SET_NULL, blank=True, null=True)  # don't delete answer if user is removed (just make anon)
    question = models.ForeignKey('Questions', on_delete=models.CASCADE, blank=True, null=True)  # should delete answer if question is deleted
    score = models.BigIntegerField(default=0)
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Answers'
        
class Votes(models.Model):
    # Vote choices for vote type
    VOTE_CHOICES = [
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    ] 

    vote_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('Users', on_delete=models.CASCADE)  # Link to the user who voted
    answer = models.ForeignKey('Answers', on_delete=models.CASCADE)  # Link to the answer being voted on
    vote_type = models.CharField(max_length=8, choices=VOTE_CHOICES)  # Upvote or Downvote
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Votes'
        unique_together = ('user', 'answer')
        
class Communities(models.Model):
    community_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey('Users', on_delete=models.SET_NULL, blank=True, null=True)
    title = models.TextField(unique=True)
    description = models.TextField()
    member_count = models.BigIntegerField(default=0)
    avatar_url = models.URLField(blank=True, null=True)
    tags = models.ManyToManyField('Tags', related_name='communities', blank=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    search_vector = SearchVectorField(null=True, blank=True)

    # Add search functionality once that is complete
    class Meta:
        db_table = 'Communities'
        indexes = [
            GinIndex(fields=['search_vector']),  # GIN index
        ]  
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_search_vector()

    def update_search_vector(self):
        """
        Update the search_vector field based on title, description, and tags.
        """
        # Aggregate tag names into a single string
        tag_names = " ".join(self.tags.values_list('name', flat=True))
        
        # Combine title, description, and tag names
        combined_text = f"{self.title} {self.description} {tag_names}"

        # Update the search_vector using PostgreSQL's to_tsvector function
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE "Communities"
                SET search_vector = to_tsvector('english', %s)
                WHERE community_id = %s
                """,
                [combined_text, str(self.community_id)]
            )

class Projects(models.Model):
    project_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey('Users', on_delete=models.SET_NULL, blank=True, null=True)
    public = models.BooleanField()
    title = models.TextField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    repo_full_name = models.TextField(null=True)
    tags = models.ManyToManyField('Tags', related_name='projects', blank=True) 

    class Meta:
        db_table = 'Projects'


class Questions(models.Model):
    question_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asker = models.ForeignKey('Users', on_delete=models.SET_NULL, blank=True, null=True)
    related_project = models.ForeignKey(Projects, on_delete=models.SET_NULL, blank=True, null=True)
    related_community = models.ForeignKey(Communities, on_delete=models.SET_NULL, blank=True, null=True)
    code_context = models.TextField(blank=True, null=True)
    code_context_full_pathname = models.TextField(blank=True, null=True)
    code_context_line_number = models.IntegerField(blank=True, null=True)
    title = models.TextField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField('Tags', related_name='questions', blank=True)

    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        db_table = 'Questions'
        indexes = [
            GinIndex(fields=['search_vector']),
            GinIndex(fields=['title'], name='title_trgm', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['description'], name='description_trgm', opclasses=['gin_trgm_ops']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_search_vector()

    def update_search_vector(self):
        """
        Update the search_vector field based on title, description, and tags.
        """
        # Aggregate tag names into a single string
        tag_names = " ".join(self.tags.values_list('name', flat=True))
        
        # Combine title, description, and tag names
        combined_text = f"{self.title} {self.description} {tag_names}"

        # Update the search_vector using PostgreSQL's to_tsvector function
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE "Questions"
                SET search_vector = to_tsvector('english', unaccent(%s))
                WHERE question_id = %s
                """,
                [combined_text, str(self.question_id)]
            )


class Tags(models.Model):
    tag_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Tags'
        indexes = [
            GinIndex(fields=['name'], name='tags_name_trgm', opclasses=['gin_trgm_ops']),
        ]


class Users(models.Model):
    user = models.OneToOneField('AuthUser', on_delete=models.CASCADE, primary_key=True, default=uuid.uuid4)
    username = models.TextField(unique=True)
    reputation = models.BigIntegerField()
    profile_image_url = models.URLField(null=True, blank=True)  # URL to image in Supabase
    reputation = models.BigIntegerField(default=0)

    class Meta:
        db_table = 'Users'

class AuthUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Add any other fields that are needed in the Supabase auth table

    class Meta:
        managed = False  # Indicating that Django should not manage this table
        db_table = 'auth"."users'
        
class UserRoles(models.Model):
    # Role choices for role type
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ] 

    role = models.OneToOneField('Users', on_delete=models.CASCADE, primary_key=True, default=uuid.uuid4)  # Change 'User' to 'Users'
    role_type = models.CharField(max_length=5, choices=ROLE_CHOICES, default='user')

    class Meta:
        db_table = 'UserRoles'

class Comments(models.Model):
    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expert = models.ForeignKey('Users', on_delete=models.SET_NULL, blank=True, null=True)               # don't delete comment if user is removed (just make anon)
    answer = models.ForeignKey('Answers', on_delete=models.CASCADE, blank=True, null=True)          # should delete comment if answer is deleted
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Comments'

class CommunityMembers(models.Model):
    community = models.ForeignKey('Communities', on_delete=models.CASCADE)  # delete user from community if community is deleted
    user = models.ForeignKey('Users', on_delete=models.CASCADE)  # delete user from community if user is removed
    community_reputation = models.BigIntegerField(default=0)
    contributions = models.BigIntegerField(default=0)

    class Meta:
        db_table = 'CommunityMembers'
        constraints = [
            models.UniqueConstraint(fields=['community', 'user'], name='unique_community_user')
        ]


class Notifications(models.Model):
    NOTIFICATION_TYPES = [
        ('question_answered', 'New Answer'),
        ('answer_commented', 'New Comment'),
        ('question_upvoted', 'Answer Accepted'),
        ('answer_accepted', 'Mention'),
        ('mention', 'Vote Received'),
        ('community_accepted', 'Community Accepted'),
        ('community_rejected', 'Community Rejected'),
    ]

    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    # References to related entities
    question = models.ForeignKey('Questions', on_delete=models.CASCADE, null=True, blank=True)
    answer = models.ForeignKey('Answers', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('Comments', on_delete=models.CASCADE, null=True, blank=True)
    community = models.ForeignKey('Communities', on_delete=models.CASCADE, null=True, blank=True)
    community_title = models.TextField(null=True, blank=True)
    actor = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, related_name='notifications_triggered')
    
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Notifications'
        # queries which filter/sort on (recipient, -createt_at) or (recipient, read) will be faster using indexes
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'read'])
        ]