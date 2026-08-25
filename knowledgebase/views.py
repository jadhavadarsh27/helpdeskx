from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Article


@login_required
def article_list(request):
    articles = Article.objects.filter(is_published=True).select_related('category')
    q = request.GET.get('q')
    if q:
        articles = articles.filter(Q(title__icontains=q) | Q(body__icontains=q) | Q(summary__icontains=q))
    paginator = Paginator(articles, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'knowledgebase/article_list.html', {'page_obj': page_obj, 'q': q or ''})


@login_required
def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    Article.objects.filter(pk=article.pk).update(views=article.views + 1)
    return render(request, 'knowledgebase/article_detail.html', {'article': article})
