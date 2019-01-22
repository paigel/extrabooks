
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Create your views here.
from django.urls import reverse_lazy
from django.views.generic import CreateView,UpdateView
from django.views.generic import DetailView

from books.models import Book
from .forms import CustomUserCreationForm
from .models import CustomUser
from books.models import Book

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

class EditProfileView(LoginRequiredMixin,UserPassesTestMixin,UpdateView):
    model = CustomUser
    fields = ['username', 'zip_code', 'first_name','last_name', 'avatar']
    template_name = 'settings.html'
    login_url = 'login'

    def test_func(self):
        obj = self.get_object()
        print(obj)
        return  obj == self.request.user
'''
    def form_valid(self, form):
        profile_image = CustomUser.avatar(
            image=self.get_form_kwargs().get('files')['image'])
        profile_image.save()
        self.id = profile_image.id

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('profile', kwargs={'pk': self.id})
'''
class ProfieView(DetailView):
    model = CustomUser
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        print("kwargs: ", kwargs["object"])
        username = kwargs["object"]
        context['book_list'] = Book.objects.filter(seller__username = username)
        return context
