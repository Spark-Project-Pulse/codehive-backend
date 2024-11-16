from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpRequest
from rest_framework import status
from ..supabase_utils import get_supabase_client, create_bucket_if_not_exists
from ..models import Users, UserRoles
from ..serializers import UserSerializer, UserRolesSerializer

'''POST Operations'''

@api_view(["POST"])
def createUser(request: HttpRequest) -> JsonResponse:
    """
    Create a user using the UserSerializer to validate
    and save the incoming data.

    Args:
        request (HttpRequest): The incoming HTTP request containing the data.
    
    Returns:
        JsonResponse: A response with the created user's ID if successful,
        or validation errors if the data is invalid.
    """
    serializer = UserSerializer(data=request.data)  # Deserialize and validate the data
    if serializer.is_valid():
        user = serializer.save()  # Save the valid data as a new User instance
        
        UserRoles.objects.create(role=user, role_type='user') # Assign the user role to the new user
        return JsonResponse(
            {"user_id": user.user_id}, status=status.HTTP_201_CREATED
        )
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def changeReputationByAmount(request: HttpRequest, user_id: str, amount: str) -> JsonResponse:
    """
    Increase the reputation of a user by the passed in amount, identified by their user ID.

    Args:
        request (HttpRequest): The incoming HTTP request.
        user_id (str): The ID of the user whose reputation should be increased.
        amount (int): The amount of reputation that should change.

    Returns:
        JsonResponse: A response indicating the new reputation or an error message.
    """
    try:
        user = get_object_or_404(Users, user_id=user_id)  # Retrieve the user by ID
        amount = int(amount)  # Cast amount to int
        user.reputation += amount  # Change the reputation
        user.save()  # Save the updated user object
        return JsonResponse(
            {"user_id": user.user_id, "new_reputation": user.reputation},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Unable to change reputation", "details": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
'''GET Operations'''

@api_view(["GET"])
def getUserById(request: HttpRequest, user_id: str) -> JsonResponse:
    """
    Retrieve a single user by their ID and serialize it to JSON format.

    Args:
        request (HttpRequest): The incoming HTTP request.
        user_id (str): The ID of the user to retrieve.

    Returns:
        JsonResponse: A response containing serialized data for the requested user.
    """
    user = get_object_or_404(Users, user_id=user_id)  # Get the user or return 404
    serializer = UserSerializer(user)  # Serialize the single instance to JSON
    return JsonResponse(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
def getUserByUsername(request: HttpRequest, username: str) -> JsonResponse:
    """
    Retrieve a single user by their username and serialize it to JSON format.

    Args:
        request (HttpRequest): The incoming HTTP request.
        username (str): The username of the user to retrieve.

    Returns:
        JsonResponse: A response containing serialized data for the requested user.
    """
    user = get_object_or_404(Users, username=username)  # Get the user or return 404
    serializer = UserSerializer(user)  # Serialize the single instance to JSON
    return JsonResponse(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
def getUserRoleById(request: HttpRequest, user_id: str) -> JsonResponse:
    """
    Retrieve the role of a user by their user ID.

    Args:
        request (HttpRequest): The incoming HTTP request.
        user_id (str): The ID of the user to retrieve the role for.

    Returns:
        JsonResponse: A response containing the user role of the requested user.
    """
    user_role = get_object_or_404(UserRoles, role=user_id)  # Get the user role or return 404
    serializer = UserRolesSerializer(user_role)  # Serialize the single instance to JSON
    return JsonResponse(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
def userExists(request: HttpRequest, user_id: str) -> JsonResponse:
    """
    Check if a user exists in the database by their user ID.

    Args:
        request (HttpRequest): The incoming HTTP request.
        user_id (str): The ID of the user to check.

    Returns:
        JsonResponse: A response indicating whether the user exists.
    """
    try:
        exists = Users.objects.filter(user_id=user_id).exists()  # Check if the user exists
        return JsonResponse({"exists": exists}, status=status.HTTP_200_OK)  # Return a 200 OK response with a boolean result
    except Exception as e:
        return JsonResponse(
            {"error": "An error occurred", "details": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )  # Log the error and return a 500 response for unexpected errors
        
'''PUT Operations'''

@api_view(["PUT"])
@parser_classes([MultiPartParser])  # To handle file uploads
def updateProfileImageById(request: HttpRequest, user_id: str) -> JsonResponse:
    """
    Updates the specified user's profile image

    Args:
        request (HttpRequest): The incoming HTTP request.
        user_id (str): The ID of the user to update profile image on

    Returns:
        JsonResponse: A response containing serialized data for the requested user.
    """

    # Get supabase client
    supabase = get_supabase_client()

    # Get the user or return 404
    user = get_object_or_404(Users, user_id=user_id)  

    # Get image file from request
    image_file = request.FILES.get('profile_image')
    if not image_file:
        return JsonResponse({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
    image_content = image_file.read()

    # Create bucket if it does not exist
    if not create_bucket_if_not_exists('profile-images'):
        return JsonResponse({'error': 'Could not ensure bucket exists.'}, status=500)
    
    # Set the upload path in Supabase Storage
    upload_path = f"{user_id}/profile-image"

    # Upload the image file to Supabase Storage, replaces current profile pic if it exists
    response = supabase.storage.from_("profile-images").upload(
        file=image_content, 
        path=upload_path, 
        file_options={"content-type": image_file.content_type, "upsert": "true"},
        )

    if response.path:
        # Store the image URL in the user's profile
        user.profile_image_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/profile-images/{upload_path}"
        user.save()
        serializer = UserSerializer(user)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK)
    else:
        return JsonResponse({"error": "Failed to upload image"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)