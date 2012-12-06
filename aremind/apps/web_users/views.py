from django.shortcuts import redirect

def welcome(request):
    if request.user.is_superuser:
        return redirect('smscouchforms.views.download')
    elif request.user.has_perm('dashboard.pbf_view'):
        return redirect('pbf_dashboard')
    elif request.user.has_perm('dashboard.fadama_view'):
        return redirect('fadama_dashboard')
    else:
        return redirect('smscouchforms.views.download')
