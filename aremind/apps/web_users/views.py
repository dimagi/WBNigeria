from django.shortcuts import redirect

def welcome(request):
    if request.user.is_superuser:
        return redirect('smscouchforms.views.download')
    elif all(request.user.has_perm(perm) for perm in ('dashboard.pbf_view', 'dashboard.fadama_view')):
        return redirect('dashboard/')
    elif request.user.has_perm('dashboard.pbf_view'):
        return redirect('pbf_dashboard')
    elif request.user.has_perm('dashboard.fadama_view'):
        return redirect('fadama_dashboard')
    else:
        return redirect('account/login/') #'radpisms_login') # can't get url reverse to work
