# Club demo para las capturas de la landing. SOLO para el entorno de desarrollo local.
#   docker compose exec -T backend python manage.py shell < landing/demo/seed_demo.py
# Es idempotente: si el club «demo» ya existe, lo borra y lo vuelve a crear con fechas relativas a hoy.
# Todos los nombres y datos son inventados. Se niega a correr sin DEBUG (nunca en PRE ni PRO).
import random
from datetime import datetime, time, timedelta
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import connection
from django.utils import timezone
from django_tenants.utils import schema_context
from PIL import Image, ImageDraw, ImageFilter

from apps.accounts.models import User
from apps.bookings.models import Booking, Closure, Session, Space
from apps.bookings.services import BookingService, ClosureService, SpaceService
from apps.bookings.tasks import ensure_upcoming_sessions
from apps.clubs.models import Club, Domain
from apps.clubs.services import ClubService
from apps.memberships.models import Membership
from apps.news.models import News
from apps.polls.models import Poll, PollOption, PollResponse, PollSelection
from apps.tickets.models import Ticket, TicketMessage
from apps.walls.models import Route, RouteAscent, RouteComment, RouteHold, Wall
from apps.walls.services import WallService
from core.exceptions import DomainError

if not settings.DEBUG:
    raise SystemExit('El club demo solo se crea en desarrollo (DEBUG=True).')

CODE = 'demo'
PASSWORD = 'Demo-presa-2026'
MEMBERS = [
    ('sara', 'Sara', 'Martín'), ('pablo', 'Pablo', 'Ruiz'), ('irene', 'Irene', 'Soler'),
    ('marcos', 'Marcos', 'Vidal'), ('nuria', 'Nuria', 'Campos'), ('hugo', 'Hugo', 'Ferrer'),
    ('alba', 'Alba', 'Moreno'), ('jorge', 'Jorge', 'Navarro'), ('carla', 'Carla', 'Ibáñez'),
    ('sergio', 'Sergio', 'Prieto'), ('marta', 'Marta', 'Gil'), ('dani', 'Dani', 'Ortega'),
    ('lucia', 'Lucía', 'Herrera'), ('alex', 'Álex', 'Romero'),
]
HOLD_COLORS = [(232, 196, 40), (45, 112, 200), (214, 58, 52), (60, 160, 90), (40, 40, 40),
               (140, 80, 170), (236, 128, 40), (232, 112, 160)]
rng = random.Random(2026)


def try_book(*, user: User, session: Session, now) -> None:
    """Reserva como lo haría el socio; si las reglas no lo permiten (solape, ya reservada), se salta."""
    try:
        BookingService.book_session(user=user, session_id=session.pk, now=now)
    except DomainError:
        pass


def wall_photo(*, seed: int, size=(1200, 900)) -> tuple[ContentFile, list[tuple[float, float]]]:
    """Dibuja una pared de paneles con presas de colores y devuelve la foto y los centros (0–1) de las presas."""
    local = random.Random(seed)
    width, height = size
    image = Image.new('RGB', size, (214, 204, 186))
    draw = ImageDraw.Draw(image)
    for row in range(0, height, 150):
        for col in range(0, width, 200):
            tone = local.randint(-10, 10)
            draw.rectangle((col, row, col + 199, row + 149), fill=(212 + tone, 201 + tone, 182 + tone), outline=(180, 170, 152))
            for bolt_x in range(col + 25, col + 200, 50):
                for bolt_y in range(row + 25, row + 150, 50):
                    draw.ellipse((bolt_x - 3, bolt_y - 3, bolt_x + 3, bolt_y + 3), fill=(120, 112, 100))
    centers = []
    for _ in range(85):
        x, y = local.randint(40, width - 40), local.randint(40, height - 40)
        radius = local.randint(14, 34)
        color = local.choice(HOLD_COLORS)
        points = [(x + radius * local.uniform(.7, 1.2) * dx, y + radius * local.uniform(.7, 1.2) * dy)
                  for dx, dy in ((1, 0), (.7, .7), (0, 1), (-.7, .7), (-1, 0), (-.7, -.7), (0, -1), (.7, -.7))]
        draw.polygon([(px + 4, py + 5) for px, py in points], fill=(150, 140, 125))
        draw.polygon(points, fill=color)
        centers.append((x / width, y / height))
    image = image.filter(ImageFilter.SMOOTH)
    buffer = BytesIO()
    image.save(buffer, 'JPEG', quality=88)
    return ContentFile(buffer.getvalue()), centers


def route_holds(centers: list[tuple[float, float]], *, seed: int, count: int = 8) -> list[dict]:
    """Elige presas de la foto de abajo arriba: dos de inicio, un pie, manos y una de final."""
    local = random.Random(seed)
    band = sorted(local.sample(centers, count), key=lambda point: -point[1])
    kinds = ['start', 'start', 'foot', *['hand'] * (count - 4), 'finish']
    return [{'x': round(x, 4), 'y': round(y, 4), 'radius': 0.035, 'kind': kind} for (x, y), kind in zip(band, kinds)]


def reset_club() -> Club:
    """Borra el club demo si existe y lo crea de nuevo con su administrador."""
    connection.set_schema_to_public()
    old = Club.objects.filter(code=CODE).first()
    if old is not None:
        Domain.objects.filter(tenant=old).delete()
        old.delete(force_drop=True)
    return ClubService.create_club(name='Rocódromo Demo', code=CODE, admin_email='admin@demo.presa.test',
                                   admin_password=PASSWORD)


def create_people(today) -> dict[str, User]:
    """Crea los socios, el personal y sus cuotas; Sara tiene la cuota a 5 días de terminar."""
    admin = User.objects.get(email='admin@demo.presa.test')
    admin.first_name, admin.last_name, admin.must_change_password = 'Admin', 'Demo', False
    admin.role, admin.is_staff, admin.is_superuser = User.Role.ADMIN, True, True
    admin.save()
    people = {'admin': admin}
    signed = timezone.now() - timedelta(days=30)
    for key, first, last in MEMBERS:
        people[key] = User.objects.create_user(email=f'{key}@demo.presa.test', password=PASSWORD, first_name=first,
                                               last_name=last, waiver_signed_at=signed)
        ends_on = today + timedelta(days=5) if key == 'sara' else today + timedelta(days=rng.randint(20, 300))
        Membership.objects.create(user=people[key], starts_on=today - timedelta(days=60), ends_on=ends_on,
                                  auto_renew=key != 'sara')
    people['staff'] = User.objects.create_user(email='equipo@demo.presa.test', password=PASSWORD, first_name='Equipo',
                                               last_name='Demo', role=User.Role.STAFF, waiver_signed_at=signed)
    return people


def create_agenda(people: dict[str, User], now) -> None:
    """Espacios, un cierre semanal y reservas para que la agenda tenga movimiento (y una franja llena)."""
    specs = [('bloque', 'Bloque', 24), ('cuerda', 'Cuerda', 16), ('gimnasio', 'Gimnasio', 8)]
    spaces = [SpaceService.save_space(space=Space(slug=slug, name=name, max_capacity=capacity, slot_minutes=60,
                                                  opens_at=time(9), closes_at=time(23)))
              for slug, name, capacity in specs]
    closure = Closure(reason='Limpieza', kind=Closure.Kind.WEEKLY, weekday=4, start_time=time(9), end_time=time(11),
                      valid_from=now.date())
    closure.save()
    ensure_upcoming_sessions()
    ClosureService.apply_closures(now=now)
    members = [people[key] for key, _, _ in MEMBERS]
    sessions = Session.objects.filter(starts_at__gt=now, starts_at__lt=now + timedelta(days=6),
                                      is_cancelled=False).order_by('starts_at')
    for session in sessions:
        local_hour = timezone.localtime(session.starts_at).hour
        busy = 17 <= local_hour <= 21
        for member in rng.sample(members, rng.randint(4, 11) if busy else rng.randint(0, 3)):
            if member is not people['sara']:
                try_book(user=member, session=session, now=now)
    gym = spaces[2]
    evening = sessions.filter(space=gym, starts_at__gte=now + timedelta(hours=2)).order_by('starts_at').first()
    if evening is not None:
        for member in members[1:]:
            if not Booking.objects.filter(user=member, session=evening).exists():
                try_book(user=member, session=evening, now=now)
    tomorrow_evening = timezone.make_aware(datetime.combine(now.date() + timedelta(days=1), time(18)))
    sara_slot = Session.objects.filter(space=spaces[0], starts_at=tomorrow_evening).first()
    if sara_slot is not None:
        try_book(user=people['sara'], session=sara_slot, now=now)


def create_walls(people: dict[str, User], today, now) -> None:
    """Dos multipresa con vías de los socios y tres bloques; uno, proyecto de Sara, se desmonta en 3 días."""
    authors = [people[key] for key in ('pablo', 'irene', 'marcos', 'nuria', 'hugo', 'alba')]
    route_names = [('La diagonal', '6a'), ('Amarilla de calentar', '5'), ('El techo', '6c+'), ('Regletas', '6b'),
                   ('Travesía larga', '6a+'), ('Explosiva', '7a')]
    for order, (slug, name, seed) in enumerate([('desplome', 'Desplome', 11), ('placa', 'Placa', 23)], start=1):
        photo, centers = wall_photo(seed=seed)
        wall = Wall(slug=slug, name=name, kind=Wall.Kind.MULTI_HOLD, order=order,
                    description='Panel de 45°' if slug == 'desplome' else 'Placa vertical para técnica de pies')
        wall.image.save(f'{slug}.jpeg', photo, save=False)
        WallService.save_wall(wall=wall)
        for index, (route_name, grade) in enumerate(route_names if order == 1 else route_names[:3]):
            route = Route.objects.create(wall=wall, author=authors[index % len(authors)], grade=grade,
                                         name=route_name if order == 1 else f'{route_name} II',
                                         comment='Cuidado con el pie del final.' if index == 0 else '')
            RouteHold.objects.bulk_create([RouteHold(route=route, **hold)
                                           for hold in route_holds(centers, seed=seed * 10 + index)])
            for member in rng.sample(list(people.values())[1:12], rng.randint(1, 6)):
                RouteAscent.objects.create(route=route, user=member, style=rng.choice(['flash', 'done', 'done', 'project']))
    first = Route.objects.get(wall__slug='desplome', name='La diagonal')
    RouteComment.objects.create(route=first, author=people['irene'], body='Muy bonita, el paso del medio es la clave.')
    RouteComment.objects.create(route=first, author=people['sara'], body='¡Por fin la saqué! Gracias por montarla.')
    boulders = [('la-fisura', 'La fisura', '6b', 3, 31), ('techo-amarillo', 'Techo amarillo', '7a', 10, 37),
                ('el-tobogan', 'El tobogán', '5+', None, 43)]
    for order, (slug, name, grade, days, seed) in enumerate(boulders, start=3):
        photo, _ = wall_photo(seed=seed, size=(900, 1100))
        wall = Wall(slug=slug, name=name, kind=Wall.Kind.SINGLE_PROBLEM, grade=grade, order=order,
                    expires_on=today + timedelta(days=days) if days is not None else None,
                    description='Bloque de la zona de entrada')
        wall.image.save(f'{slug}.jpeg', photo, save=False)
        WallService.save_wall(wall=wall)
    mark = {'la-fisura': 'project', 'el-tobogan': 'flash'}
    for slug, style in mark.items():
        RouteAscent.objects.create(route=Route.objects.get(wall__slug=slug, is_wall_problem=True),
                                   user=people['sara'], style=style)
    Wall.objects.exclude(slug='el-tobogan').update(created_at=now - timedelta(days=20))


def create_club_life(people: dict[str, User], now) -> None:
    """Noticias, encuestas y un ticket respondido para que Inicio tenga novedades."""
    staff = people['staff']
    News.objects.create(title='Nueva zona de bloque en la entrada', author=staff, is_pinned=True,
                        published_at=now - timedelta(hours=3),
                        content='Hemos montado tres bloques nuevos en la zona de entrada. ¡A probarlos!')
    News.objects.create(title='Cierre por limpieza los viernes de 9 a 11', author=staff,
                        published_at=now - timedelta(days=1), content='Aprovechamos para cepillar presas.')
    News.objects.create(title='Quedada de escalada el domingo', author=staff, published_at=now - timedelta(days=4),
                        content='Salida a roca para todos los niveles. Apúntate en recepción.')
    poll = Poll.objects.create(title='¿Ampliamos el horario de invierno?', author=staff, ends_at=now + timedelta(days=6))
    options = PollOption.objects.bulk_create([PollOption(poll=poll, text=text, order=index) for index, text in
                                              enumerate(['Abrir a las 8:00', 'Cerrar a las 23:30', 'Así está bien'])])
    for member in [people[key] for key in ('pablo', 'irene', 'marcos', 'nuria', 'hugo', 'alba', 'jorge')]:
        response = PollResponse.objects.create(poll=poll, user=member)
        PollSelection.objects.create(response=response, option=rng.choice(options))
    ticket = Ticket.objects.create(author=people['sara'], subject='La ducha de la izquierda no calienta',
                                   last_message_at=now - timedelta(hours=1))
    TicketMessage.objects.create(ticket=ticket, author=people['sara'], body='Desde ayer sale fría.')
    TicketMessage.objects.create(ticket=ticket, author=staff, body='Gracias por avisar, mañana viene el técnico.')


club = reset_club()
with schema_context(club.schema_name):
    now = timezone.now()
    today = timezone.localdate(now)
    people = create_people(today)
    create_agenda(people, now)
    create_walls(people, today, now)
    create_club_life(people, now)
print(f'Club demo listo: /club/{CODE}/ · sara@demo.presa.test / {PASSWORD} · admin@demo.presa.test / {PASSWORD}')
