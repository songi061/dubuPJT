from datetime import timezone

from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import *
from django.core.paginator import Paginator
from django.core.files.storage import  FileSystemStorage
from datetime import timezone

from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from .models import *
from django.core.paginator import Paginator
from django.core.files.storage import  FileSystemStorage

import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, GlobalAveragePooling1D
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing import image
from PIL import Image

import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from django.core.cache import cache
from django.utils import timezone
from .utils import get_tokens_for_user
import requests
import uuid

load_dotenv()
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Create your views here.

def index(request) :
    print('debug >>> mainApp /index')
    return render(request, 'mainpage/index.html')


def scalp(request) :
    print('debug >>> mainApp /scalp')
    return render(request, 'mainpage/scalp.html')


def shampoo(request) :
    print('debug >>> mainApp /shampoo')
    return render(request, 'mainpage/shampoo.html')


def my(request) :
    print('debug >>> mainApp /my')
    return render(request, 'mainpage/my.html')


def login(request) :
    print('debug >>> mainApp /login')
    print('debug >>> request method ', request.method)
    try:
        if request.method == "POST":
            username = request.POST.get("id")
            password = request.POST.get("pwd")
            print("debug params >>> ", username, password)

            # 로그인 실패 기록 확인
            fail_count_key = f"login_fail_{username}"
            fail_count = cache.get(fail_count_key, 0)

            # 임계값 초과 시
            if fail_count >= 11:
                last_attempt_time = cache.get(f"{fail_count_key}_time")
                if last_attempt_time and timezone.now() < last_attempt_time + timezone.timedelta(minutes=5):
                    return HttpResponse("로그인이 일시적으로 차단되었습니다. 5분 후에 다시 시도해주세요.")

            try:
                user = User_tbl.objects.get(user_id=username, user_pwd=password)
                print('debug >>> user ', user)
                if user is not None: # 로그인 성공
                    # 실패 카운트 초기화
                    cache.delete(fail_count_key)
                    cache.delete(f"{fail_count_key}_time")
                    # 로그인 처리
                    request.session['user_id'] = user.user_id
                    print('debug >>> 로그인 성공!')
                    return redirect('index')
            except User_tbl.DoesNotExist:
                print('debug >>> 로그인 실패 1: ', request)
                cache.set(fail_count_key, fail_count + 1, timeout=300)  # 실패 카운트 증가
                print('fail_count: ', fail_count)
                if fail_count == 0:
                    cache.set(f"{fail_count_key}_time", timezone.now(), timeout=300)
                return render(request, 'mainpage/login.html', {'message': '아이디와 비밀번호를 다시 확인해주세요'})
        else:
            print('debug >>> 로그인 실패 2')
            return render(request, 'mainpage/login.html')
    except Exception as e:
        print('debug >>> 예외 발생 2: ', e)
        return render(request, 'mainpage/login.html')


def join(request) :
    print('debug >>> mainApp /join')
    return redirect('register')


# media 폴더에 사진 업로드
def upload(request) :
    print('debug >>>> upload ')
    file = request.FILES['image']
    print('debug >>>> img ' , file , file.name)
    fs = FileSystemStorage()
    fileName = fs.save(file ,file)
    print('debug >>>> filename ', fileName)
    img_file = Image.open(file)
    img_file = img_file.resize((60, 80))
    img = image.img_to_array(img_file)
    img = img.reshape(1, img.shape[0], img.shape[1], img.shape[2])
    # 모델 위치는 본인 컴퓨터 환경에 맞춰서 재설정 부탁드립니다 !
    pre_train_model = keras.models.load_model('C:/Users/user/PycharmProjects/Team2PJT/rootWEB/mainApp/static/hair_predict_model2')
    guess = pre_train_model.predict(img)
    labels = ['양호', '경증 비듬', '중등도 비듬', '중증 비듬', '경증 탈모', '중등도 탈모', '중증 탈모']
    links  = ['/shampoo', '/dandruff', '/dandruff', '/dandruff', '/loss', '/loss', '/loss']
    predicted_label = labels[np.argmax(guess)]
    links_label     = links[np.argmax(guess)]
    return render(request, 'mainpage/scalp_result.html', {'predicted_label': predicted_label, 'fileName' : fileName, 'links_label' : links_label})



def shampooButton(request):
    return render(request, 'mainpage/loss.html')

def loss(request) :
    print('debug >>> mainApp /loss')
    return render(request, 'mainpage/loss.html')

def dandruff(request) :
    print('debug >>> mainApp /dandruff')
    return render(request, 'mainpage/dandruff.html')


def logout_view(request):
    if 'user_id' in request.session:
        del request.session['user_id']
        print('debug >>> user deleted')
    return redirect('index')


def register(request):
    try:
        if request.method == 'POST':
            id = request.POST['id']
            pwd = request.POST['pwd']
            email = request.POST['email']
            User_tbl.objects.create(user_id=id, user_pwd=pwd, user_email=email)
            return redirect('login')
        return render(request, 'mainpage/register.html')
    except Exception as e:
        print('debug >>> Exception: ', e)
        return render(request, 'mainpage/register.html')


def find_my_account(request) :
    print('debug >> mainApp /find_pwd')
    return render(request, 'mainpage/find_my_account.html')


def google_auth(request):
    # Google OAuth 설정
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email'],
        redirect_uri='http://127.0.0.1:8000/auth/google/callback'
    )

def check_user_id(request):
    user_id = request.GET.get('id', None)
    is_taken = User_tbl.objects.filter(user_id=user_id).exists()
    return JsonResponse({'is_taken': is_taken})


# def KAKAO_JS_KEY(request):
#     context = {
#         'KAKAO_JS_KEY': os.environ.get('KAKAO_JS_KEY')
#     }
#     return render(request, 'register.html', context)


# def kakao_callback(request):
#     print('debug >> view - mainApp/kakao_callback')
#     # code = request.GET.get('code')
#     REST_API_key = os.getenv("REST_API_key")
#     token_request = requests.get(
#         f"https://kauth.kakao.com/oauth/authorize?response_type=code&client_id={REST_API_key}&redirect_uri=http://127.0.0.1:8000/oauth/kakao/callback"
#     )
#
#     token_json = token_request.json()
#     print('debug >>> token_json :', token_json)
#     error = token_json.get("error", None)
#     if error is not None:
#         raise Exception("Can't get authorization code.")
#
#     access_token = token_json.get("access_token")
    # 이제 access_token을 사용하여 사용자 정보를 가져오고, 로그인 처리를 합니다.
    #
    # # 카카오 사용자 정보 요청
    # profile_request = requests.get(
    #     "https://kapi.kakao.com/v2/user/me",
    #     headers={"Authorization": f"Bearer {access_token}"},
    # )
    # profile_json = profile_request.json()
    # kakao_account = profile_json.get("kakao_account")
    # email = kakao_account.get("email", None)
    #
    # # 여기서부터는 사용자의 이메일을 사용하여 사용자를 식별하고,
    # # 우리 시스템에 로그인 처리를 수행합니다.
    # # 예를 들어, 사용자 모델을 조회하고 세션을 만드는 등의 작업을 할 수 있습니다.
    # # 만약 사용자가 새로운 사용자라면, 계정을 생성하는 과정도 필요할 수 있습니다.
    #
    # # 예를 들어, Django의 auth 시스템을 사용하면 다음과 같이 할 수 있습니다.
    # try:
    #     user = User.objects.get(email=email)  # 가정: User 모델에서 이메일을 사용하여 사용자를 조회
    # except User.DoesNotExist:
    #     # 새 사용자라면, 계정을 생성할 수 있습니다.
    #     user = User.objects.create_user(username=email, email=email)
    #     user.save()
    #
    # # 사용자 로그인 처리
    # login(request, user)
    #
    # # 로그인 후 리디렉션할 페이지로 이동
    # return redirect('index')


from django.views import View
class KakaoSignInCallBackView(View):
    def get(self, request):
        # uri에 잘 출력되는지 확인하기 (디버그용 코드 1)
        # app_key= os.getenv('REST_API_key')
        # redirect_uri   = "http://127.0.0.1:8000/oauth/kakao/callback"
        # kakao_auth_api = "https://kauth.kakao.com/oauth/authorize?response_type=code"
        # return redirect(
        #     f'{kakao_auth_api}&client_id={app_key}&redirect_uri={redirect_uri}'
        # )

        auth_code = request.GET.get('code')
        kakao_token_api = "https://kauth.kakao.com/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'client_id' : os.getenv('REST_API_KEY'),
            'redirection_uri': "http://127.0.0.1:8000/oauth/kakao/callback",
            'code': auth_code,
        }

        token_response = requests.post(kakao_token_api, data=data)
        # 카카오 인증 서버와의 티키타카 (디버그용 코드 2)
        # return JsonResponse({"token": token_response.json()})
        print('debug >>> token_response: ', token_response.json())

        access_token = token_response.json().get('access_token')
        print('debug >>> access_token: ', access_token)

        kakao_user_api     = "https://kapi.kakao.com/v2/user/me"
        header             = {"Authorization": f"Bearer ${access_token}"}
        user_info_response = requests.get(kakao_user_api, headers=header)
        print('debug >>> user_info_response: ', user_info_response)

        user_information   = requests.get(kakao_user_api, headers=header).json()
        print('debug >>> user_information: ', user_information)
        # 디버그용 코드임.
        # return JsonResponse({"user_info": user_info_response.json()})

        kakao_id           = user_information["id"]
        kakao_email        = user_information["kakao_account"]["email"]
        profile_image_url  = user_information["properties"]["profile_image"]
        print('debug >>> kakao id & email & profile image: ', kakao_id, kakao_email, profile_image_url)

        # # 사용자 찾기 또는 생성
        # if not User_tbl.objects.filter(user_id=kakao_id).exists():
        #     user = User_tbl.objects.create(user_id=kakao_id, user_pwd=uuid.uuid4().hex, user_email=kakao_email)
        #     print('debug >>> 계정 생성과 함께 임의의 비밀번호가 설정되었습니다. user: ', user)
        #     # user.save() => create() 메서드는 실제로 save()를 내부적으로 호출하기 때문에 이 부분은 필요하지 않을 수도 있다.
        # else:
        #     user = User_tbl.objects.get(user_id=kakao_id)
        #     print('debug >>> 이미 존재하는 계정이라 아이디를 가져왔습니다.')
        # # user, created = User_tbl.objects.get_or_create(user_id=kakao_id, defaults={'user_email':kakao_email})
        #
        # # JWT 토큰 발급
        # token = get_tokens_for_user(user)
        # print('debug >>> kakao_token: ', token)
        #
        # # 필요한 경우 추가적인 사용자 정보 설정
        # # if created:
        # #     # 새 사용자의 경우, 임의의 안전한 비밀번호 설정
        # #     user.set_password(uuid.uuid4().hex)
        # #     print('debug >>> 임의의 비밀번호가 설정되었습니다. => view-get()')
        # #     user.save()
        # # print('debug >>> user & token: ', {'user': {'username': user.user_id, 'email': user.user_email}, 'token': token})
        # # return JsonResponse({'user': {'username': user.user_id, 'email': user.user_email}, 'token': token})


        request.session['user_id'] = kakao_id
        return redirect('/scalp/')
def kakao_api(request):
    print('debug >>> mainApp/kakao_api()')
    context = {
        'KAKAO_JS_KEY': os.environ.get('KAKAO_JS_KEY')
    }
    return render(request, 'register.html', context)

# 내일 할 것.
# 남은 Auth 로직 처리
#
# 우리의 목적은 카카오 계정으로 우리 서비스에 회원가입 하거나 로그인 하는 것이었으므로, 남은 로직을 View에 구현해 주면 되겠다.
#
# 간단히 로직만 생각해보자면,
#
# 위에서 진행한 내용으로 유저의 Kakao "ID"를 알아낸다.
# 해당 카카오 ID를 갖는 유저를 우리의 유저 DB에서 찾아본다.
# 존재하면 로그인 시키고 JWT 토큰을 발행해준다.
# 존재하지 않으면 회원가입 시키고 JWT 토큰을 발행해준다.
# 이렇게 하면 프론트에서 단순히 Django 백엔드의 소셜 로그인 엔드포인트로 연결해주는것 만으로도 카카오 계정을 통한 소셜 로그인이 가능하다.