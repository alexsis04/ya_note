from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client, TestCase
from django.utils.text import slugify

from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestLogic(TestCase):

    def setUp(self):
        self.author = User.objects.create(username='author')
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.note = Note.objects.create(
            title='Старый заголовок',
            text='Старый текст',
            slug='old-slug',
            author=self.author
        )
        self.form_data = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'new-slug'
        }
        self.not_author = User.objects.create(username='not_author')
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    def test_user_can_create_note(self):
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.latest('pk')
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        client = Client()
        url = reverse('notes:add')
        response = client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        url = reverse('notes:add')
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        """Тест: Автор может редактировать свою заметку."""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, self.form_data)
        self.assertRedirects(
            response,
            reverse('notes:success'),
            fetch_redirect_response=False
        )
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.not_author_client.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(pk=self.note.pk)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(
            response,
            reverse('notes:success'),
            fetch_redirect_response=False
        )
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.not_author_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)


class TestEmptySlug(TestCase):
    def setUp(self):
        self.author = User.objects.create(username='author2')
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.form_data_without_slug = {
            'title': 'Заголовок для теста пустого slug',
            'text': 'Текст'
        }

    def test_empty_slug(self):
        url = reverse('notes:add')
        response = self.author_client.post(
            url,
            data=self.form_data_without_slug)
        self.assertRedirects(
            response,
            reverse('notes:success'),
            fetch_redirect_response=False
        )
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.latest('pk')
        expected_slug = slugify(self.form_data_without_slug['title'])
        self.assertEqual(new_note.slug, expected_slug)