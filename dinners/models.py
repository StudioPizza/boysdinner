# dinners/models.py
from django.db import models

class Boy(models.Model):
    name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100, blank=True)
    birthday = models.DateField(null=True, blank=True)
    reliability = models.FloatField(default=1.0)
    last_hosted = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Dinner(models.Model):
    date = models.DateField(null=True, blank=True)  # nullable => placeholder allowed
    restaurant = models.CharField(max_length=120, blank=True)
    host = models.ForeignKey(Boy, on_delete=models.PROTECT, related_name='hosted_dinners')
    attendees = models.ManyToManyField(Boy, through='Attendance', related_name='dinners_attended')

    class Meta:
        ordering = ['-date', '-id']  # newest first; placeholders sorted by id

    def __str__(self):
        return f"{self.date or 'TBD'} — {self.restaurant or 'TBD'}"


class Attendance(models.Model):
    STATUS_CHOICES = [('present', 'Present'), ('excused', 'Excused'), ('absent', 'Absent')]
    dinner = models.ForeignKey(Dinner, on_delete=models.CASCADE, related_name='attendance_records')
    boy = models.ForeignKey(Boy, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')

    class Meta:
        unique_together = ('dinner', 'boy')

    def __str__(self):
        return f"{self.boy} -> {self.dinner} ({self.status})"
