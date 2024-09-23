from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import F
from typing import Any

from django.views.generic import ListView, DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views import View

from .models import Choice, Question, Reply
from .forms import QuestionForm, ReplyForm


class QuestionListView(ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"
    model = Question

    def get_queryset(self):
        query = super().get_queryset()
        return query.filter(
            pub_date__lte=timezone.now()
            ).order_by('-pub_date')
    
    def get_context_data(self, **kwargs):
        # Add the form to the context data for the GET request
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form', QuestionForm())
        context['title'] = 'wisqer'
        return context


class QuestionCreateView(LoginRequiredMixin, FormView):
    form_class = QuestionForm
    template_name = "polls/index.html"
    success_url = reverse_lazy('polls:index')
    login_url = reverse_lazy('accounts:login')
    redirect_field_name = 'next'

    def form_valid(self, form):
        new_question = form.save(commit=False)
        new_question.user = self.request.user
        new_question.pub_date = timezone.now()
        new_question.save()

        return HttpResponseRedirect(
            reverse('polls:detail', args=(new_question.id,))
        )
    
    def form_invalid(self, form):
        latest_question_list = Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')
        context = self.get_context_data(form=form)
        context['latest_question_list'] = latest_question_list
        return self.render_to_response(context)


class QuestionReplyView(TemplateView):
    template_name = "polls/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question_obj = get_object_or_404(
            Question.objects.filter(
                pub_date__lte=timezone.now()
                ), pk=kwargs["question_id"]
        )
        context['question'] = question_obj
        context['reply_form'] = ReplyForm()

        context['latest_reply_list'] = Reply.objects.filter(
        pub_date__lte=timezone.now(),
        question=question_obj
        ).order_by('-pub_date')

        context['title'] = question_obj.question_text
        return context


class ReplyCreateView(LoginRequiredMixin, FormView):
    form_class = ReplyForm
    template_name = "polls/detail.html"
    login_url = reverse_lazy('accounts:login')
    redirect_field_name = 'next'

    def get_success_url(self):
        return reverse_lazy('polls:detail', args=(self.kwargs['question_id'],))

    def form_valid(self, form):
        question = get_object_or_404(Question, pk=self.kwargs['question_id'])
        new_reply = form.save(commit=False)
        new_reply.user = self.request.user
        new_reply.pub_date = timezone.now()
        new_reply.question = question
        new_reply.save()

        return super().form_valid(form)
    
    def form_invalid(self, form):
        question = get_object_or_404(Question, pk=self.kwargs['question_id'])
        context = self.get_context_data(form=form)
        context['question'] = question
        context['reply_form'] = form

        latest_reply_list = Reply.objects.filter(
            pub_date__lte=timezone.now(),
            question=question
        ).order_by('-pub_date')

        context['latest_reply_list'] = latest_reply_list
        context['title'] = f"Could not reply to {question.question_text}"
        return self.render_to_response(context)


class ResultsView(DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(
            pk=request.POST["choice"])
        
    except (KeyError, Choice.DoesNotExist):
        # redisplay the question voting form.
        context = {
            "question":question,
            "error_message": "You didn't select a choice.",
        }
        return render(request, "polls/detail.html", context)
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        return HttpResponseRedirect(reverse("polls:results", \
                                            args=(question.id,)))
