from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator

FIRST_PLAYER_TO_MOVE = 'F'
SECOND_PLAYER_TO_MOVE = 'S'
FIRST_PLAYER_WINS = 'W'
SECOND_PLAYER_WINS = 'L'
DRAW = 'D'

GAME_STATUS_CHOICES = (
    (FIRST_PLAYER_TO_MOVE, 'First player to move'),
    (SECOND_PLAYER_TO_MOVE, 'Second player to move'),
    (FIRST_PLAYER_WINS, 'First player wins'),
    (SECOND_PLAYER_WINS, 'Second player wins'),
    (DRAW, 'Draw')
)

BOARD_SIZE = 3


class GamesQuerySet(models.QuerySet):
    def games_for_user(self, user):
        return self.filter(
            Q(first_player=user) | Q(second_player=user)
        )

    def active(self):
        return self.filter(Q(status=FIRST_PLAYER_TO_MOVE) | Q(status=SECOND_PLAYER_TO_MOVE))


class Game(models.Model):
    first_player = models.ForeignKey(User, related_name="games_first_player", on_delete=models.CASCADE)
    second_player = models.ForeignKey(User, related_name="games_second_player", on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, default=FIRST_PLAYER_TO_MOVE, choices=GAME_STATUS_CHOICES)

    objects = GamesQuerySet.as_manager()

    def board(self):
        board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        for move in self.move_set.all():
            board[move.y][move.x] = move
        return board

    def is_user_move(self, user):
        return (user == self.first_player and self.status == FIRST_PLAYER_TO_MOVE) or\
               (user == self.second_player and self.status == SECOND_PLAYER_TO_MOVE)

    def update_after_move(self, move):
        """Update the status of the game, given the last move"""
        self.status = self._get_game_status_after_move(move)

    def _get_game_status_after_move(self, move):
        x, y = move.x, move.y
        board = self.board()
        if (board[y][0] == board[y][1] == board[y][2]) or \
           (board[0][x] == board[1][x] == board[2][x]) or \
           (board[0][0] == board[1][1] == board[2][2]) or \
           (board[0][2] == board[1][1] == board[2][0]):
            return FIRST_PLAYER_WINS if move.by_first_player else SECOND_PLAYER_WINS
        if self.move_set.count() >= BOARD_SIZE**2:
            return DRAW
        return SECOND_PLAYER_TO_MOVE if self.status == FIRST_PLAYER_TO_MOVE else FIRST_PLAYER_TO_MOVE

    def get_absolute_url(self):
        """constructs absolute URL mapping to route name on urls.py"""
        return reverse('gameplay_detail', args=[self.id])

    def new_move(self):
        if self.status not in "{0}{1}".format(FIRST_PLAYER_TO_MOVE, SECOND_PLAYER_TO_MOVE):
            raise ValueError("Cannot make move on finished game")

        return Move(game=self, by_first_player=self.status == FIRST_PLAYER_TO_MOVE)

    def __str__(self):
        return "{0} vs {1}".format(self.first_player, self.second_player)


class Move(models.Model):

    position_validators = [
        MinValueValidator(0),
        MaxValueValidator(BOARD_SIZE-1)
    ]

    x = models.IntegerField(validators=position_validators)
    y = models.IntegerField(validators=position_validators)
    comment = models.CharField(max_length=300, blank=True)
    by_first_player = models.BooleanField(editable=True)
    game = models.ForeignKey(Game, editable=False, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super(Move, self).save(*args, **kwargs)
        self.game.update_after_move(self)
        self.game.save()

    def __str__(self):
        return "X:{0}-Y{1}".format(self.x, self.y)

    def __eq__(self, other):
        if other is None:
            return False
        return other.by_first_player == self.by_first_player
