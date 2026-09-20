from django.core.management.base import BaseCommand

from how_it_works.models import ProcessSection, ProcessStep

STEPS = [
    (1, "Inquiry & date check",
     "Tell us the date and venue. We confirm availability within a day and send our package guide."),
    (2, "Planning call",
     "We walk through your ceremony order, family shot list, and any must-have moments."),
    (3, "The big day",
     "Our team arrives ahead of schedule and works quietly through every ceremony."),
    (4, "Edit & delivery",
     "A preview set within a week, full gallery and films within 4–6 weeks."),
]


class Command(BaseCommand):
    help = "Seeds the original static 'How it works' content into the database."

    def handle(self, *args, **options):
        section = ProcessSection.load()
        section.kicker = "How it works"
        section.heading = "From first message to final gallery"
        section.save()

        for order, (num, title, desc) in enumerate(STEPS, start=1):
            ProcessStep.objects.update_or_create(
                step_number=num,
                defaults={
                    "title": title,
                    "description": desc,
                    "order": order,
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Process section + steps seeded successfully."))
