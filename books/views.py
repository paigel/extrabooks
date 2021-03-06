from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView,DeleteView,CreateView
from .models import Book, Category, BookImage
from django.urls import reverse_lazy
from users.models import CustomUser
from django.shortcuts import render,redirect
from django.http import Http404,HttpResponseForbidden
from django.shortcuts import get_object_or_404
from taggit.models import Tag
import sys,redis,isbntools
from .forms import BookCreatebyISBNForm,BookCreatebyISBNForm2, ImageFormSet
from .googlebookapi import get_book_by_isbn
from .goodread import get_rating_by_isbn
from django.conf import settings
from actions.utils import create_action
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.contrib.sessions.models import Session
from urllib.parse import urlparse
import urllib,os
from django.core.files import File
from .location import get_city_location
from django.contrib.gis.db.models.functions import Distance
from django.contrib import messages

#connect to redis
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r = redis.from_url(redis_url)
redistogo_url = os.getenv('REDISTOGO_URL', None)
if redistogo_url == None:
  redis_url = '127.0.0.1:6379'
else:
  redis_url = redistogo_url
  redis_url = redis_url.split('redis://redistogo:')[1]
  redis_url = redis_url.split('/')[0]
  REDIS_PWD, REDIS_HOST = redis_url.split('@', 1)
  redis_url = "%s?password=%s" % (REDIS_HOST, REDIS_PWD)
session_opts = { 'session.type': 'redis', 'session.url':
                redis_url, 'session.data_dir': './cache/',
                'session.key': 'appname', 'session.auto': True, }

class BookSearchMixin:
    def get_queryset(self):
        q = self.request.GET.get('q')
        books=Book.objects.all()
        if q: #return a filtered quertset
            books= Book.objects.filter(
            Q(name__icontains=q)|Q(description__icontains=q)|Q(isbn__icontains=q))
        #no q is specified so we return queryset
        return books

class BookListView(BookSearchMixin,ListView):
    model = Book
    #tag = None
    queryset = model.objects.order_by('-date')
    select_related = ("seller", "category")
    template_name = 'books/book_list.html'


def book_list_by_tag(request,tag_slug=None):
    tag = None
    tag = get_object_or_404(Tag, slug=tag_slug)
    book_list = Book.objects.filter(tags__in=[tag])
    return render(request, 'books/book_list.html', {'book_list':book_list,
                                                'tag':tag})

def book_list_category(request,category_slug=None):
    category = None
    print(category_slug)
    category= get_object_or_404(Category,slug=category_slug)
    book_list = Book.objects.filter(category__in=[category])
    return render(request, 'books/categories.html', {'book_list':book_list,
                                                'category':category})

class MyBookListView(ListView):
    model = Book
    template_name = 'books/my_book_list.html'

    def get_queryset(self):
        u = CustomUser.objects.get(username=self.request.user)
        return Book.objects.filter(seller=u)

class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #increment total book views by 1
        context["total_views"] = r.incr('context.book:{}:views'.format(context['book'].id))
        #increment book ranking by 1
        r.zincrby('book_ranking',context['book'].id,1)
        book = kwargs["object"]
        context['images'] = BookImage.objects.filter(book__name = book)
        return context


class BookDeleteView(LoginRequiredMixin,UserPassesTestMixin, SuccessMessageMixin,DeleteView):
    model = Book
    template_name = 'books/book_delete.html'
    success_url = reverse_lazy('books:book_list')
    login_url = 'login'
    success_message = "%(name)s was delete successfully"
    def test_func(self):
        obj = self.get_object()
        return obj.seller == self.request.user

class BookUpdateView(LoginRequiredMixin,UserPassesTestMixin,SuccessMessageMixin,UpdateView):
    model = Book
    fields = ['name', 'description', 'price', 'picture', 'category']
    template_name = 'books/book_edit.html'
    login_url = 'login'
    success_message = " %(name)s Updated successfully!"
    def test_func(self):
        obj = self.get_object()
        return obj.seller == self.request.user

class BookCreateView(LoginRequiredMixin,SuccessMessageMixin,CreateView):
    model = Book
    fields = ['name', 'description', 'price', 'isbn' ,'picture', 'category']
    template_name = 'books/book_new.html'
    success_url = reverse_lazy('books:book_list')
    login_url = 'login'
    success_message = "%(calculated_field)s was created successfully"

    def form_valid(self,form):
        form.instance.seller = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        create_action(self.request.user,'selling a book', self.object)
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data,
                                           calculated_field=self.object.name)
def book_create_by_ISBN(request):
    form = BookCreatebyISBNForm(data=request.GET)
    if request.method == 'POST':
        form = BookCreatebyISBNForm(data=request.POST)
        if form.is_valid():
            isbn = form.cleaned_data['isbn']
            isbn= isbn.replace('-', '').replace(' ', '')
            request.session['isbn'] = isbn
            return redirect('books:book_by_isbn')
    return render(request,'books/book_new_by_ISBN.html',{'form':form})

def book_create_by_ISBN_2(request):
    form = BookCreatebyISBNForm2(request.GET)
    isbn = request.session['isbn']
    book_object = get_book_by_isbn(isbn)
    name = book_object['title']
    description = book_object['description']
    picture_url = book_object['thumbnail']
    result = urllib.request.urlretrieve(picture_url)
    rating = get_rating_by_isbn(isbn)['average_rating']
    ratings_count = get_rating_by_isbn(isbn)['ratings_count']
    if request.method == 'POST':
        form = BookCreatebyISBNForm2(request.POST)
        formset = ImageFormSet(request.POST, request.FILES,
                               queryset=BookImage.objects.none())
        if form.is_valid() and formset.is_valid():
            book=Book(name =name,
                        isbn= isbn,
                        picture = picture_url[10:],
                        description = description,
                        rating = rating,
                        rating_counts = ratings_count,
                        category = form.cleaned_data['category'],
                        price = form.cleaned_data['price'],
                        city = form.cleaned_data['city'],
                        condition = form.cleaned_data['condition'],
                        seller = request.user)
            if result:
                book.picture.save(
                        os.path.basename(picture_url),
                        File(open(result[0], 'rb')))
            book.save()
            for form in formset.cleaned_data:
                #this helps to not crash if the user
                #do not upload all the photos
                if form:
                    image = form['image']
                    photo = BookImage(book=book, image=image)
                    photo.save()
            messages.success(request, 'Your book was created.') # ignored
        return redirect(book.get_absolute_url())
    else:
        form = BookCreatebyISBNForm2()
        formset = ImageFormSet(queryset=BookImage.objects.none())
    return render(request,'books/book_by_isbn.html', {'form':form,
                                                        'formset':formset,
                                                    'isbn':isbn,
                                                    'name': name,
                                                    'picture':picture_url,
                                                    'description':description,
                                                    'rating':rating,
                                                    'ratings_count':ratings_count})

class BookListbyCategoryView(ListView):
    model = Category
    template_name = 'books/categories.html'

def sort(request):
    term = request.GET.get('sort')
    books = Book.objects.order_by(term)
    return render(request, 'books/categories.html', {'book_list':books})

def book_ranking(request):
    #get image ranking dectionary
    book_ranking = r.zrange('book_ranking',0,-1, desc = True)[:10]
    book_ranking_ids = [int(id) for id in book_ranking]
    #get most viewed images
    most_viewed = list(Book.objects.filter(id__in=book_ranking_ids))
    most_viewed.sort(key=lambda x: book_ranking_ids.index(x.id))
    return render(request,
                    'books/ranking.html',
                    {'section':'books',
                    'most_viewed':most_viewed})

def get_distance(request):
    city = request.GET.get('city')
    user_location =get_city_location(city)
    books = Book.objects.annotate(distance=Distance('location', user_location)).order_by('distance')
    return render(request, 'books/book_list.html', {'book_list':books})
