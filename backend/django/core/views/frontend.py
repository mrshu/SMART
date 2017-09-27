from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.db import transaction
from django.core.exceptions import PermissionDenied

import hashlib
import pandas as pd

from core.models import (User, Project, ProjectPermissions, Model, Data, Label,
                         DataLabel, DataPrediction, Queue, DataQueue, AssignedData)
from core.forms import ProjectForm, ProjectUpdateForm, PermissionsFormSet, LabelFormSet
from core.templatetags import project_extras


def md5_hash(obj):
    """Return MD5 hash hexdigest of obj; returns None if obj is None"""
    if obj is not None:
        return hashlib.md5(obj.encode('utf-8', errors='ignore')).hexdigest()
    else:
        return None

# Index
class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'smart/smart.html'

# Projects
class ProjectList(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/list.html'
    paginate_by = 10
    ordering = 'name'

    def get_queryset(self):
        # Projects user created
        qs1 = Project.objects.filter(creator=self.request.user)

        # Projects user has permissions for
        qs2 = Project.objects.filter(projectpermissions__user=self.request.user)

        qs = qs1 | qs2

        return qs.distinct().order_by(self.ordering)

class ProjectDetail(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/detail.html'

    def get_object(self, *args, **kwargs):
        obj = super(ProjectDetail, self).get_object(*args, **kwargs)

        # Check user permissions before showing project detail page
        if project_extras.proj_permission_level(obj, self.request.user) == 0:
            raise PermissionDenied('You do not have permission to view this project')
        return obj


class ProjectCreate(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create.html'

    def get_context_data(self, **kwargs):
        data = super(ProjectCreate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['labels'] = LabelFormSet(self.request.POST, prefix='label_set')
            data['permissions'] = PermissionsFormSet(self.request.POST, prefix='permissions_set', form_kwargs={'action':'create', 'user': self.request.user})
        else:
            data['labels'] = LabelFormSet(prefix='label_set')
            data['permissions'] = PermissionsFormSet(prefix='permissions_set', form_kwargs={'action':'create', 'user': self.request.user})
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        labels = context['labels']
        permissions = context['permissions']
        with transaction.atomic():
            if labels.is_valid() and permissions.is_valid():
                self.object = form.save(commit=False)
                self.object.creator = self.request.user
                self.object.save()
                labels.instance = self.object
                labels.save()
                permissions.instance = self.object
                permissions.save()

                f_data = form.cleaned_data.get('data', False)
                if isinstance(f_data, pd.DataFrame):
                    # Create hash of text and drop duplicates
                    f_data['hash'] = f_data[0].apply(md5_hash)
                    f_data.drop_duplicates(subset='hash', keep='first', inplace=True)

                    # Limit the number of rows to 2mil
                    f_data = f_data[:2000000]

                    # Create data objects and bulk insert into database
                    if len(f_data) > 0:
                        f_data['objects'] = f_data.apply(lambda x: Data(text=x[0], project=self.object, hash=x['hash']), axis=1)
                        Data.objects.bulk_create(f_data['objects'].tolist())

                return redirect(self.get_success_url())
            else:
                return self.render_to_response(context)

class ProjectUpdate(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectUpdateForm
    template_name = 'projects/create.html'

    def get_object(self, *args, **kwargs):
        obj = super(ProjectUpdate, self).get_object(*args, **kwargs)

        # Check user permissions before showing project update page
        if project_extras.proj_permission_level(obj, self.request.user) == 0:
            raise PermissionDenied('You do not have permission to view this project')
        return obj

    def get_context_data(self, **kwargs):
        data = super(ProjectUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['permissions'] = PermissionsFormSet(self.request.POST, instance=data['project'], prefix='permissions_set', form_kwargs={'action': 'update', 'creator':data['project'].creator, 'user': self.request.user})
        else:
            data['permissions'] = PermissionsFormSet(instance=data['project'], prefix='permissions_set', form_kwargs={'action': 'update', 'creator':data['project'].creator, 'user': self.request.user})
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        permissions = context['permissions']
        with transaction.atomic():
            if permissions.is_valid():
                self.object = form.save()
                permissions.instance = self.object
                permissions.save()

                f_data = form.cleaned_data.get('data', False)
                if isinstance(f_data, pd.DataFrame):
                    # Create hash of text and drop duplicates
                    f_data['hash'] = f_data[0].apply(md5_hash)
                    f_data.drop_duplicates(subset='hash', keep='first', inplace=True)

                    # Drop any duplicates from existing data
                    existing_hashes = set(Data.objects.filter(project=self.object).values_list('hash', flat=True))
                    f_data = f_data[~f_data['hash'].isin(existing_hashes)]

                    # Limit the number of rows to 2mil (including existing data)
                    f_data = f_data[:2000000-len(existing_hashes)]

                    # Create data objects and bulk insert into database
                    if len(f_data) > 0:
                        f_data['objects'] = f_data.apply(lambda x: Data(text=x[0], project=self.object, hash=x['hash']), axis=1)
                        Data.objects.bulk_create(f_data['objects'].tolist())

                return redirect(self.get_success_url())
            else:
                return self.render_to_response(context)

class ProjectDelete(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/confirm_delete.html'
    success_url = reverse_lazy('projects:project_list')

    def get_object(self, *args, **kwargs):
        obj = super(ProjectDelete, self).get_object(*args, **kwargs)

        # Check user permissions before showing project delete page
        if project_extras.proj_permission_level(obj, self.request.user) == 0:
            raise PermissionDenied('You do not have permission to view this project')
        return obj