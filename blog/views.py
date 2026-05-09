from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import (
    Post, Project, UsesCategory, Product,
    NewsletterIssue, TimelineEntry,
)
from .forms import NewsletterForm, ContactForm


def home(request):
    posts = Post.objects.all()
    featured = posts.filter(featured=True)[:3]
    recent = posts.filter(featured=False)[:4]
    return render(request, 'home.html', {
        'featured': featured,
        'recent': recent,
        'newsletter_form': NewsletterForm(),
    })


def blog_list(request):
    tag = request.GET.get('tag', 'all')
    posts = Post.objects.all()
    tags = ['all'] + list(posts.values_list('tag', flat=True).distinct())
    if tag != 'all':
        posts = posts.filter(tag=tag)

    posts_by_year = {}
    for post in posts:
        yr = post.year
        posts_by_year.setdefault(yr, []).append(post)
    years_sorted = sorted(posts_by_year.items(), key=lambda x: x[0], reverse=True)

    return render(request, 'blog/list.html', {
        'posts_by_year': years_sorted,
        'tags': tags,
        'current_tag': tag,
    })


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    return render(request, 'blog/detail.html', {'post': post})


def projects(request):
    return render(request, 'projects.html', {
        'projects': Project.objects.all(),
    })


def uses(request):
    categories = UsesCategory.objects.prefetch_related('items').all()
    return render(request, 'uses.html', {'categories': categories})


def products(request):
    prods = Product.objects.prefetch_related('bullets').all()
    return render(request, 'products.html', {'products': prods})


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related('bullets'), slug=slug)
    return render(request, 'products/detail.html', {'product': product})


def newsletter(request):
    issues = NewsletterIssue.objects.all()[:4]
    return render(request, 'newsletter.html', {
        'issues': issues,
        'newsletter_form': NewsletterForm(),
    })


def newsletter_issue(request, number):
    issue = get_object_or_404(NewsletterIssue, number=number)
    return render(request, 'newsletter/detail.html', {'issue': issue})


def hire_me(request):
    return render(request, 'hire_me.html', {
        'contact_form': ContactForm(),
    })


def about(request):
    timeline = TimelineEntry.objects.all()
    return render(request, 'about.html', {'timeline': timeline})


@require_POST
def subscribe(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        from .models import NewsletterSubscriber
        obj, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if not created and not obj.is_active:
            obj.is_active = True
            obj.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'message': 'Subscribed!'})
        return redirect(request.META.get('HTTP_REFERER', '/'))
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def contact(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'message': 'Message sent!'})
        return redirect(request.META.get('HTTP_REFERER', '/hire-me/'))
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
    return redirect(request.META.get('HTTP_REFERER', '/hire-me/'))
