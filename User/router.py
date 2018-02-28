""" Adel Liu 180111

用户API路由
"""
from django.views.decorators.gzip import gzip_page

from Base.error import Error
from Base.response import error_response, response, Method
from User.controller import UserController as Controller


@gzip_page
def rt_user(request):
    """ /api/user/

    GET:    get_my_info, 获取我的信息
    POST:   create_user, 创建用户
    PUT:    modify_user, 修改用户信息
    """
    options = {
        Method.GET: "获取我的信息",
        Method.POST: "创建用户",
        Method.PUT: "修改用户信息",
    }
    if request.method == Method.OPTIONS:
        return response(body=options, allow=True)

    if request.method == Method.GET:
        return Controller.get_my_info(request)
    if request.method == Method.POST:
        return Controller.create_user(request)
    if request.method == Method.PUT:
        return Controller.modify_user(request)
    return error_response(Error.ERROR_METHOD)


@gzip_page
def rt_user_token(request):
    """ /api/user/token

    POST:   auth_token, 获取登录token
    """
    options = {
        Method.POST: "获取登录token"
    }
    if request.method == Method.OPTIONS:
        return response(body=options, allow=True)

    if request.method == Method.POST:
        return Controller.auth_token(request)
    return error_response(Error.ERROR_METHOD)


@gzip_page
def rt_user_avatar(request):
    """ /api/user/avatar

    GET:    upload_avatar_token, 获取用户上传头像到七牛的token
    POST:   upload_avatar_callback, 七牛上传用户头像的回调函数
    """
    options = {
        Method.GET: "获取用户上传头像到七牛的token",
        Method.POST: "七牛上传用户头像的回调函数",
    }
    if request.method == Method.OPTIONS:
        return response(body=options, allow=True)

    if request.method == Method.GET:
        return Controller.upload_avatar_token(request)
    if request.method == Method.POST:
        return Controller.upload_avatar_callback(request)
    return error_response(Error.ERROR_METHOD)


@gzip_page
def rt_username(request, username):
    """ /api/user/@:username

    GET:    get_user_info, 获取用户信息
    DELETE: delete_user, 删除用户
    """
    options = {
        Method.GET: "获取用户信息",
        Method.DELETE: "删除用户",
    }
    if request.method == Method.OPTIONS:
        return response(body=options, allow=True)

    if request.method == Method.GET:
        return Controller.get_user_info(request, username)
    if request.method == Method.DELETE:
        return Controller.delete_user(request, username)
    return error_response(Error.ERROR_METHOD)
