from django.test import TestCase, Client
from django.urls import reverse
from notes.models import Note
from django.contrib.auth import get_user_model
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='author')
        cls.reader = User.objects.create(username='reader')
        cls.user = User.objects.create(username='testUser')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.user
        )
        cls.slug = cls.notes.slug

    def test_note_in_list_for_author(self):
        url = reverse('notes:list')   
        response = self.user_client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.notes, object_list)

    def test_note_not_in_list_for_another_user(self):
        reader_client = Client()
        reader_client.force_login(self.reader)
        url = reverse('notes:list')
        response = reader_client.get(url)
        object_list = response.context['object_list']
        self.assertNotIn(self.notes, object_list)

    def test_note_form_pages_contains_form(self):
        urls = {
            'add': reverse('notes:add'),
            'edit': reverse('notes:edit', args=[self.slug]),
        }
        for url in urls.values():
            response = self.user_client.get(url)
            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], NoteForm)
