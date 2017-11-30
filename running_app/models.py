from __future__ import unicode_literals
import mimetypes
import uuid
import os
from os.path import splitext
from django.template.defaultfilters import slugify
from django.db import models
from django.contrib.auth.models import User
from django.utils.deconstruct import deconstructible
from running_project.settings import MEDIA_ROOT

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat

@deconstructible
class FileValidator(object):
    extension_message = _("Extension '%(extension)s' not allowed. Allowed extensions are: '%(allowed_extensions)s.'")
    mime_message = _("MIME type '%(mimetype)s' is not valid. Allowed types are: %(allowed_mimetypes)s.")
    min_size_message = _('The current file %(size)s, which is too small. The minumum file size is %(allowed_size)s.')
    max_size_message = _('The current file %(size)s, which is too large. The maximum file size is %(allowed_size)s.')

    def __init__(self, *args, **kwargs):
        self.allowed_extensions = kwargs.pop('allowed_extensions', None)
        self.allowed_mimetypes = kwargs.pop('allowed_mimetypes', None)
        self.min_size = kwargs.pop('min_size', 0)
        self.max_size = kwargs.pop('max_size', None)

    def __call__(self, value):
        # Check the extension
        ext = splitext(value.name)[1][1:].lower()
        if self.allowed_extensions and not ext in self.allowed_extensions:
            message = self.extension_message % {
                'extension' : ext,
                'allowed_extensions': ', '.join(self.allowed_extensions)
            }

            raise ValidationError(message)

        # Check the content type
        mimetype = mimetypes.guess_type(value.name)[0]
        if self.allowed_mimetypes and not mimetype in self.allowed_mimetypes:
            message = self.mime_message % {
                'mimetype': mimetype,
                'allowed_mimetypes': ', '.join(self.allowed_mimetypes)
            }

            raise ValidationError(message)

        # Check the file size
        filesize = len(value)
        if self.max_size and filesize > self.max_size:
            message = self.max_size_message % {
                'size': filesizeformat(filesize),
                'allowed_size': filesizeformat(self.max_size)
            }

            raise ValidationError(message)

        elif filesize < self.min_size:
            message = self.min_size_message % {
                'size': filesizeformat(filesize),
                'allowed_size': filesizeformat(self.min_size)
            }

            raise ValidationError(message)

    def __eq__(self, other):
        return isinstance(other, FileValidator)


@deconstructible
class UploadToPathAndRename(object):

    def __init__(self, path):
        self.sub_path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        if ext == 'jpeg':
            ext = 'jpg'
        file_prefix = str(uuid.uuid4())[-12:]
        filename = '{}.{}'.format(file_prefix, ext)
        # return the whole path to the file
        return os.path.join(self.sub_path, filename)

@deconstructible
class UploadGPXAndRename(object):

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        file_prefix = str(uuid.uuid4())[-12:]
        filename = '{}.{}'.format(file_prefix, ext)
        # return the whole path to the file
        return "gpx_files/" + filename


class UserProfile(models.Model):
    user = models.OneToOneField(User)

    website = models.URLField(blank=True)
    picture = models.ImageField(upload_to=UploadToPathAndRename(os.path.join(MEDIA_ROOT, 'profile_images')), validators=[FileValidator(min_size=1*500, max_size=10*1024*1024, allowed_mimetypes=('image/png', 'image/jpg', 'image/jpeg',), allowed_extensions=('png', 'jpg', 'jpeg',))], blank = True)

    def __str__(self):
        return self.user.username

    def __unicode__(self):
        return self.user.username

class GpxFile(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    gpx_file = models.FileField(upload_to=UploadGPXAndRename(os.path.join(MEDIA_ROOT, 'gpx_files')), max_length=300, validators=[FileValidator(min_size=1*500, max_size=10*1024*1024, allowed_mimetypes=('application/gpx+xml', 'application/octet-stream'), allowed_extensions=('gpx'))], blank = True)
