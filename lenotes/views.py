from django.urls import reverse
from django.http import HttpResponseRedirect, Http404, StreamingHttpResponse, HttpResponse
from django.shortcuts import render

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from lenotes.models import Group, Diary, Invitation, Imgele, Textele
from users.models import UserInfo, Message
from lenotes.forms import GroupForm, DiaryForm, InvitationForm
from users.views import update_userInfo_unread_count

from datetime import datetime
from PIL import Image

import json

def check_user(request, group, flag): 
    """
        flag 0 检查是不是群主
        flag 1 检查是不是群成员
    """
    if flag == 0 and request.user != group.owner:
        raise Http404
    elif flag == 1 and request.user not in group.members.all():
        raise Http404


@login_required
def delete_ajax(request):
    """
        用来删除Imgele或者Texele
    """
    del_id = request.POST.get("del_id")
    if(del_id[0]=='t'):
        de = Textele.objects.get(id= int(del_id[3:]))
        de.delete()
    elif(del_id[0]=='p'):
        de = Imgele.objects.get(id= int(del_id[3:]))
        de.delete()
    return HttpResponse('')


@login_required
def upload_ajax(request):
    """
        处理ajax发来的json数据，更新数据库中Imgele和Texele的css属性值
    """
    data = json.loads(request.body.decode('utf-8'))
    for key,value in data.items():
        if key[0]=='t':
            idx = int(key[3:])
            tex = Textele.objects.get(id = idx)
            tex.content = value['content']
            s = value['x']
            tex.x = float(s[:len(s)-2])
            s = value['y']
            tex.y = float(s[:len(s)-2])
            tex.zindex = int(value['z'])
            s = value['fontsize']
            tex.fontsize = int(s[:len(s)-2])
            tex.fontcolor = value['fontcolor']
            tex.save()
        elif key[0]=='p':
            idx = int(key[3:])
            pic = Imgele.objects.get(id = idx)
            s = value['x']
            pic.x = float(s[:len(s)-2])
            s = value['y']
            pic.y = float(s[:len(s)-2])
            s = value['w']
            pic.w = float(s[:len(s)-2])
            s = value['h']
            pic.h = float(s[:len(s)-2])
            pic.zindex = int(value['z'])
            pic.save()
    return HttpResponse('')



def index(request):
    """ 主页 """
    if request.user.is_authenticated:
        update_userInfo_unread_count(request.user)
    return render(request, 'lenotes/new_index.html')

def about_us(request):
    return render(request, 'lenotes/about_us.html')

@login_required
def group(request, group_id):
    """群组主页"""
    year = datetime.now().year
    month = datetime.now().month
    return HttpResponseRedirect(reverse('lenotes:diary_month', args=[group_id, year, month, 1]))

@login_required   
def diary_month(request, group_id, year, month, styleSelect):
    """ 筛选1个月的日记 ， 根据styleSelect的模式选择要渲染的html"""
    get_group = Group.objects.get(id=group_id)
    check_user(request, get_group, 1)
    tdiary = get_group.diary_set.order_by('-date_added')
    createJudge = False
    if tdiary.count()==0:
        createJudge = True
    elif tdiary[0].date_added.year != datetime.now().year or tdiary[0].date_added.month != datetime.now().month\
        or tdiary[0].date_added.day != datetime.now().day:
        createJudge = True  

    diarys = get_group.diary_set.filter(date_added__year=year, date_added__month = month)
    odiarys = diarys.order_by('date_added')    
    lastMonth, lastYear, nextMonth, nextYear = 1, 1, 1, 1
    
    lastMonthJudge = True
    if tdiary.count() == 0 or month==tdiary[len(tdiary)-1].date_added.month:
        lastMonthJudge = False
    if month==1:
        lastMonth = 12
        lastYear = year-1
    else:
        lastMonth = month-1
        lastYear = year

    nextMonthJudge = True
    if month==datetime.now().month:
        nextMonthJudge = False
    
    if month==12:
        nextMonth = 1
        nextYear = year+1
    else:
        nextMonth = month+1
        nextYear = year
    
    context = {
        'group': get_group, 
        'odiarys': odiarys, 
        'createJudge': createJudge,
        'nowYear': year,
        'nowMonth': month,
        'lastMonth': lastMonth,
        'lastYear': lastYear,
        'lastMonthJudge': lastMonthJudge,
        'nextMonthJudge': nextMonthJudge,
        'nextMonth': nextMonth,
        'nextYear': nextYear,
    }
    if styleSelect == 1:
        return render(request, 'lenotes/group_diary_md.html', context)
    elif styleSelect == 2:
        return render(request, 'lenotes/group_diary.html', context)

# # 压缩图片尺寸
# def compressImage(image):
#     tmp_image = Image.open(image)
#     width = tmp_image.width 
#     height = tmp_image.height
#     rate = 1.0 # 压缩率

#     # 根据图像大小设置压缩率
#     if width >= 3000 or height >= 3000:
#         rate = 0.15  
#     elif width >= 2000 or height >= 2000:
#         rate = 0.3
#     elif width >= 1000 or height >= 1000:
#         rate = 0.7
#     elif width >= 500 or height >= 500:
#         rate = 0.9

#     width = int(width * rate)   # 新的宽
#     height = int(height * rate) # 新的高

#     tmp_image.thumbnail((width, height), Image.ANTIALIAS) # 生成缩略图
#     tmp_image.save('media/group/img/' + str(image))

@login_required
def manage(request, group_id):
    """修改群组资料，邀请功能，管理用户"""
    if request.method != 'POST':
        try:
            group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            group = Group.objects.create(id=group_id)
        group_form = GroupForm(instance = group)
    else:
        group_form = GroupForm(request.POST, request.FILES)
        if group_form.is_valid():
            try:
                group = Group.objects.get(id=group_id)
            except ObjectDoesNotExist:
                group = Group.objects.create(id=group_id)
        group.name = group_form.cleaned_data["name"]
        group.intro = group_form.cleaned_data["intro"]
        myprofile = request.FILES.get('profile',None)
        if myprofile:
            if group.profile.name != 'group/img/default.jpg':
                group.profile.delete()
            group.profile = myprofile
        group.save()
        return HttpResponseRedirect(reverse('lenotes:group', args=[group.id]))
    
    check_user(request, group, 1)
    members = group.members.all()
    memberInfos = []
    for member in members:
        info = UserInfo.objects.get(user=member)
        memberInfos.append(info)
    context = {
        'group': group,
        'memberInfos': memberInfos,
        'group_form': group_form,
    }
    return render(request, 'lenotes/manage.html' , context)

@login_required
def del_member(request, group_id, info_id):
    """ 删除成员 """
    group = Group.objects.get(id=group_id)
    check_user(request, group, 0)
    info = UserInfo.objects.get(id=info_id)
    group.members.remove(info.user)
    msg = "You have been removed from group: " + group.name
    Message.objects.create(sender = group.owner.username + "(Group Owner)", text=msg, receiver=info.user)
    return HttpResponseRedirect(reverse('lenotes:manage', args=[group_id]))

@login_required
def send_invite(request, group_id):
    """ 发送邀请 """
    if request.method == 'POST':
        try:
            invite_user = User.objects.get(username=request.POST['invite_id'])
        except ObjectDoesNotExist:
            context = {'group_id': group_id}
            return render(request, 'lenotes/userIsNotExist.html' , context)
        group = Group.objects.get(id = group_id)
        check_user(request, group, 0)
        msg = request.user.username + " invite you to join Group: " + group.name 
        Invitation.objects.create(receiver=invite_user, message=msg, groupid=group_id, is_Read=False)
        return HttpResponseRedirect(reverse('lenotes:manage', args=[group_id]))
    group = Group.objects.get(id = group_id)
    check_user(request, group, 0)
    context = { 'group_id': group_id }
    return render(request, 'lenotes/send_invite.html', context)

@login_required
def new_group(request):
    """ 创建群组 """
    if request.method != 'POST':
        form = GroupForm()
    else:
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.owner = request.user
            new_group.save()
            new_group.members.add(request.user)
            new_group.save()
            return HttpResponseRedirect(reverse('users:home'))
    
    context = { 'form': form }
    return render(request, 'lenotes/new_group.html', context)

@login_required
def del_group(request, group_id):
    """删除当前群组"""
    del_group = Group.objects.get(id=group_id)
    check_user(request, del_group, 0)
    members = del_group.members.all()
    senderName = del_group.owner.username + "(Group Owner)"
    for member in members:
        msg = "The group: " + del_group.name + " have been deleted."
        Message.objects.create(sender=senderName, text=msg, receiver=member)
    del_group.delete()
    return HttpResponseRedirect(reverse('users:home'))

@login_required
def new_diary(request, group_id):
    """ 创建日记 """
    group = Group.objects.get(id = group_id)
    check_user(request, group, 1)
    if request.method != 'POST':
        form = DiaryForm()
    else:
        form = DiaryForm(data = request.POST)
        if form.is_valid():
            new_diary = form.save(commit=False)
            new_diary.group = group
            new_diary.save()
            return HttpResponseRedirect(reverse('lenotes:group', args=[group_id]))
    context = {'group': group, 'form': form}
    return render(request, 'lenotes/new_diary.html', context)

@login_required
def edit_diary(request, group_id, diary_id):
    """ 编辑日记 """
    diary = Diary.objects.get(id = diary_id)
    if request.method == 'POST':
        obj = request.FILES.get('Imgfield',None)
        if obj:
            new_img = Imgele.objects.create(img = obj, belong = diary)
            new_img.idname = "IMG" + str(new_img.id)
            new_img.w = 100
            new_img.h = 100
            new_img.save()
        tex = request.POST.get('newText', None)
        if tex:
            new_text = Textele.objects.create(belong=diary, content=tex)
            new_text.idname = "TEXT" + str(new_text.id)
            new_text.save()
    group = Group.objects.get(id = group_id)
    check_user(request, group, 1)
    diary = Diary.objects.get(id = diary_id)

    context = {
        'group': group,
        'diary': diary,
    }
    return render(request, 'lenotes/edit_diary.html', context)

@login_required
def edit_diary_md(request, diary_id):
    """编辑既有条目"""
    diary = Diary.objects.get(id=diary_id)
    group = diary.group
    check_user(request, group, 1)
    if request.method != 'POST':
        form = DiaryForm(instance=diary)
    else:
        form = DiaryForm(instance=diary, data=request.POST)
        if form.is_valid():
            diary.diary_log = (str(datetime.now()) + "  Editor: " + str(request.user) + "\r\n") + diary.diary_log
            form.save()
            return HttpResponseRedirect(reverse('lenotes:group', args=[group.id]))
    context = {
        'diary': diary, 
        'group': group, 
        'form': form
    }
    return render(request, 'lenotes/edit_diary_md.html', context)

@login_required
def del_diary(request, diary_id):
    """删除当前群组"""
    del_diary = Diary.objects.get(id=diary_id)
    group_id = del_diary.group.id
    del_diary.delete()
    return HttpResponseRedirect(reverse('lenotes:group', args=[group_id]))


@login_required
def add_diary(request, group_id):
    """ 这个函数好像被弃用了，但是以防万一不删它 """
    group = Group.objects.get(id=group_id)
    check_user(request, group, 1)
    Diary.objects.all().create(group=group)
    return HttpResponseRedirect(reverse('lenotes:group', args=[group_id]))

@login_required
def diary_log(request, diary_id):
    """ 日记修改记录 """
    diary_log = Diary.objects.get(id=diary_id).diary_log
    context = { 'diary_log': diary_log }
    return render(request, 'lenotes/diary_log.html', context)

def readFile(filename,chunk_size=512):  
    with open(filename,'rb') as f:  
        while True:  
            c = f.read(chunk_size)  
            if c:  
                yield c  
            else:  
                break

#本地测试使用这一个文件下载
def file_download(request):
    the_file_name = 'Readme.md'                   
    filename = 'Readme.md'      
    response = StreamingHttpResponse(readFile(filename))  
    response['Content-Type'] = 'application/octet-stream'  
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)  
    return response  

#服务器上使用这一个文件下载

# def file_download(request):
#     filename = '/home/Lenote/Readme.md'
#     newfilename = 'Readme.md'
#     f =open(filename, encoding="ISO-8859-1")
#     data = f.read()
#     f.close()
#     response = HttpResponse(data, content_type='application/octet-stream') 
#     response['Content-Disposition'] = 'attachment; filename=%s' % newfilename
#     return response

