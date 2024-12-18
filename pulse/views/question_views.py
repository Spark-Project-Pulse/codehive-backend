from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpRequest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from rest_framework import status
from services.ai_model_service import check_content
from pulse.models import Questions
from ..serializers import QuestionSerializer
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.decorators import throttle_classes
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Count, Q, F
from django.db.models.functions import Greatest
from django.contrib.postgres.aggregates import StringAgg
from uuid import UUID

@api_view(["POST"])
def createQuestion(request: HttpRequest) -> JsonResponse:
    """
    Create a question using the QuestionSerializer to validate
    and save the incoming data.

    Args:
        request (HttpRequest): The incoming HTTP request containing the data.

    Returns:
        JsonResponse: A response with the created question's ID if successful,
        or validation errors if the data is invalid.
    """
    serializer = QuestionSerializer(
        data=request.data
    )  # Deserialize and validate the data
    if serializer.is_valid():
        # Content moderation
        title_text = request.data['title']
        description_text = request.data['description']
        if check_content(title_text + description_text):
            return JsonResponse({"error": "Toxic content detected in your question."}, status=status.HTTP_200_OK)
        question = serializer.save()  # Save the valid data as a new Question instance
        return JsonResponse(
            {"question_id": question.question_id}, status=status.HTTP_201_CREATED
        )
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def getAllQuestions(request: HttpRequest) -> JsonResponse:
    """
    Retrieve questions from the database with pagination, optional tag filtering, and search functionality.
    Supports sorting by views, recency, or unanswered questions first.
    """
    # Get query parameters
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    selected_tags = request.GET.getlist('tags')  # Expecting UUIDs like ?tags=uuid1&tags=uuid2
    search_query = request.GET.get('search', '').strip()
    related_hive_id = request.GET.get('related_hive_id', None)  # Optional hive filter
    sort_by = request.GET.get('sort_by', 'Recency')  # Default to recency

    # Start with all questions
    questions = Questions.objects.all()

    # Filter by hive if related_hive_id is provided
    if related_hive_id:
        try:
            questions = questions.filter(related_hive__hive_id=related_hive_id)
        except ValueError:
            return JsonResponse({'error': 'Invalid hive ID provided'}, status=status.HTTP_400_BAD_REQUEST)

    # Apply search filter if search_query is provided
    if search_query:
        search_vector = SearchQuery(search_query, search_type='websearch')
        questions = questions.annotate(
            rank=SearchRank('search_vector', search_vector)
        ).filter(search_vector=search_vector)

    # Filter questions by tags if any tags are provided
    if selected_tags:
        try:
            selected_tags = [UUID(tag_id) for tag_id in selected_tags]
        except ValueError:
            return JsonResponse({'error': 'Invalid tag IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        num_selected_tags = len(selected_tags)

        # Filter questions that have all of the selected tags
        questions = questions.filter(tags__tag_id__in=selected_tags)
        questions = questions.annotate(
            matching_tags=Count('tags', filter=Q(tags__tag_id__in=selected_tags), distinct=True)
        ).filter(matching_tags=num_selected_tags)

    # Apply the unanswered filter for 'unanswered' sort
    if sort_by == 'unanswered':
        questions = questions.filter(is_answered=False).order_by('-created_at')


    # Apply sorting logic
    if sort_by == 'Recency':
        questions = questions.order_by('-created_at')
    elif sort_by == 'Trending':
        questions = questions.order_by('-view_count')
    elif sort_by != 'Unanswered':  # If sort_by is invalid and not 'unanswered'
        return JsonResponse({'error': 'Invalid sort option'}, status=400)

    # Remove duplicates
    questions = questions.distinct()

    # Pagination
    paginator = Paginator(questions, page_size)
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = []

    serializer = QuestionSerializer(page_obj.object_list, many=True)
    response_data = {
        'questions': serializer.data,
        'totalQuestions': paginator.count,
        'totalPages': paginator.num_pages,
        'currentPage': page_number,
    }
    return JsonResponse(response_data, status=status.HTTP_200_OK)





@api_view(["GET"])
def getQuestionsByUserId(request: HttpRequest, user_id: int) -> JsonResponse:
    """
    Retrieve all questions associated with a specific user_id
    from the database and serialize them to JSON format.

    Args:
        request (HttpRequest): The incoming HTTP request.
        user_id (int): The ID of the user whose questions are to be retrieved.

    Returns:
        JsonResponse: A response containing serialized data for the user's questions.
    """
    questions = Questions.objects.filter(asker_id=user_id).order_by(
        "-created_at"
    )  # Retrieve questions for the specified user
    serializer = QuestionSerializer(
        questions, many=True
    )  # Serialize the queryset to JSON
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


@api_view(["GET"])
def getQuestionById(request: HttpRequest, question_id: str) -> JsonResponse:
    """
    Retrieve a single question by its ID and serialize it to JSON format.

    Args:
        request (HttpRequest): The incoming HTTP request.
        question_id (str): The ID of the question to retrieve.

    Returns:
        JsonResponse: A response containing serialized data for the requested question.
    """
    # Get the question or return 404
    question = get_object_or_404(Questions, question_id=question_id)

    # increase view count
    Questions.objects.filter(question_id=question_id).update(view_count=F('view_count') + 1)

    # refresh the question instance to reflect the updated view count
    question.refresh_from_db()

    # Serialize the single instance to JSON
    serializer = QuestionSerializer(question)
    return JsonResponse(serializer.data, status=status.HTTP_200_OK)


# logger = logging.getLogger(__name__)

class BurstUserRateThrottle(UserRateThrottle):
    rate = '10/min'

class BurstAnonRateThrottle(AnonRateThrottle):
    rate = '5/min'


@require_GET
@csrf_exempt 
@throttle_classes([BurstUserRateThrottle, BurstAnonRateThrottle])
def searchQuestions(request):
    # Get query parameters
    query = request.GET.get('q', '').strip()
    tags = request.GET.getlist('tags')  # Expecting tag IDs as strings
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)  # Default page size

    if not query and not tags:
        return JsonResponse(
            {"error": "No search query or tags provided."},
            status=status.HTTP_400_BAD_REQUEST
        )

    questions = Questions.objects.all()

    # Initialize combined_filters as Q() for AND logic
    combined_filters = Q()

    # Handle search query
    if query:
        # Define the search vector with weights
        search_vector = (
            SearchVector('title', weight='A') +
            SearchVector('description', weight='B') +
            SearchVector('tags__name', weight='C')
        )
        search_query = SearchQuery(query, search_type="websearch")
        
        # Annotate with full-text search rank and trigram similarities
        questions = questions.annotate(
            rank=SearchRank(search_vector, search_query),
            similarity_title=TrigramSimilarity('title', query),
            similarity_description=TrigramSimilarity('description', query),
        ).annotate(
            tag_names=StringAgg('tags__name', delimiter=' ', distinct=True)
        ).annotate(
            similarity_tags=TrigramSimilarity('tag_names', query)
        ).annotate(
            total_similarity=Greatest(
                F('similarity_title'),
                F('similarity_description'),
                F('similarity_tags')
            )
        )

        # Combine search filters using OR logic within search criteria
        search_filter = Q(search_vector=search_query) | Q(total_similarity__gt=0.05) 

        combined_filters &= search_filter

    # Handle tag filters
    if tags:
        try:
            # Convert tag IDs to UUID objects
            tag_uuids = [UUID(tag_id) for tag_id in tags]
        except ValueError:
            return JsonResponse({'error': 'Invalid tag IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        tag_filters = Q()
        for tag_uuid in tag_uuids:
            tag_filters &= Q(tags__tag_id=tag_uuid)
        
        combined_filters &= tag_filters

    # Apply the combined AND filters
    questions = questions.filter(combined_filters).distinct().order_by('-rank', '-total_similarity', '-created_at')

    # Implement Pagination
    try:
        page_number = int(page_number)
        page_size = int(page_size)
        if page_number < 1 or page_size < 1:
            raise ValueError
    except ValueError:
        return JsonResponse({'error': 'Invalid page or page_size parameter'}, status=status.HTTP_400_BAD_REQUEST)

    paginator = Paginator(questions, page_size)
    try:
        paginated_questions = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_questions = paginator.page(1)
    except EmptyPage:
        paginated_questions = paginator.page(paginator.num_pages)

    serializer = QuestionSerializer(paginated_questions.object_list, many=True)
    return JsonResponse({
        'questions': serializer.data,
        'totalQuestions': paginator.count,
        'totalPages': paginator.num_pages,
        'currentPage': page_number,
    }, status=status.HTTP_200_OK)

@api_view(["POST"])
def changeMark(request: HttpRequest, question_id: str) -> JsonResponse:
    """
    Mark a question as answered or unanswered, depending on current state

    Args:
        request (HttpRequest): The incoming HTTP request containing the data.

    Returns:
        JsonResponse: A response with the question id if successful,
        or validation errors if the data is invalid.
    """
    question = get_object_or_404(
        Questions, question_id=question_id
    )  # Get the question or return 404
    # Toggle the `is_answered` field
    question.is_answered = not question.is_answered

    # Use the serializer to validate and save the changes
    serializer = QuestionSerializer(question, data={"is_answered": question.is_answered}, partial=True)
    if serializer.is_valid():
        serializer.save()  # Save the updated question
        return JsonResponse(serializer.data, status=status.HTTP_200_OK)

    # Return validation errors if any
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["PUT"])
def updateQuestion(request: HttpRequest, question_id: str) -> JsonResponse:
    """
    Update an existing question.

    Args:
        request (HttpRequest): The incoming HTTP request containing the data.
        question_id (str): The ID of the question to update.

    Returns:
        JsonResponse: A response with the updated question's ID if successful,
        or validation errors if the data is invalid.
    """
    # Fetch the question from the database
    question = get_object_or_404(Questions, question_id=question_id)

    # Check if the asker in the request matches the question's asker
    if request.data.get("asker") != str(question.asker_id):
        return JsonResponse(
            {"error": "You are not authorized to update this question."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Check for content moderation (toxic content)
    title_text = request.data.get("title", "")
    description_text = request.data.get("description", "")
    if check_content(title_text + description_text):
        return JsonResponse({"error": "Toxic content detected in your question."}, status=status.HTTP_200_OK)

    # Update the question using the serializer
    serializer = QuestionSerializer(instance=question, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(
            {"question_id": question.question_id}, status=status.HTTP_200_OK
        )

    # Return validation errors
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
def deleteQuestion(request: HttpRequest, question_id: str) -> JsonResponse:
    """
    Delete a question by its ID.

    Args:
        request (HttpRequest): The incoming HTTP request.
        question_id (str): The ID of the question to delete.

    Returns:
        JsonResponse: A response indicating success or failure.
    """
    # Fetch the question from the database
    question = get_object_or_404(Questions, question_id=question_id)
    
    # Check if the asker in the request matches the question's asker
    if request.data.get("asker") != str(question.asker_id):
        return JsonResponse(
            {"error": "You are not authorized to update this question."},
            status=status.HTTP_403_FORBIDDEN,
        )
        
    # Delete the question
    question.delete()
    return JsonResponse(
        {"message": "Question deleted successfully"}, status=status.HTTP_200_OK
    )
