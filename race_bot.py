"""Discord bot for racing games"""

import asyncio
import io
import operator

from datetime import datetime

import discord
import yaml

from discord.ext import commands

__author__ = '4shockblast'


class Race(commands.Cog):
    """Race object

    Provides functionality to create, start, end races as well as functionality
    for racers to participate in races
    """
    RESULT_LINE_TEMPLATE = '{prev_results}{idx}. {racer} {time} {comments}\n'
    RESULT_LINE_NO_FINISH_TEMPLATE = '{prev_results}{idx}. {racer}\n'
    RESULT_FILE_LINE_TEMPLATE = '{prev_results}{idx}.|{racer}|{time}\n' \
                                '{comments}\n'
    RESULT_FILE_LINE_NO_FINISH_TEMPLATE = '{prev_results}{idx}.|{racer}\n'

    def __init__(self, _bot):
        """Initialize a race

        Race initialized to a not created state, createrace command must be
        run before the race is created
        """
        self.bot = _bot
        self._race_created = False
        self._time_created = None
        self._race_started = False
        self._time_started = None
        self._race_goal = None
        self._race_game = None
        self._race_file_name = None
        self._num_racers = None
        self._num_ready = None
        self._num_finished = None
        self._results_printed = False

        self._racer_dict = {}
        self._racer_comments_dict = {}
        self._racer_start_times_dict = {}
        self._racer_ready_dict = {}

    @commands.command(pass_context=True)
    async def createrace(self, ctx):
        """Creates the race.

        Only mods can run this command
        """
        if self.is_mod(ctx.author):
            if self._race_created:
                await ctx.send('Race already created, please end the current '
                               'race to create a new one.')
            elif self._race_started:
                await ctx.send('Race already started, please end the current '
                               'race to create a new one.')
            else:
                await ctx.send('Creating race.')
                self._time_created = datetime.utcnow()
                self._race_created = True
                self._race_file_name = 'race_{}.txt'.format(
                    self._time_created.timestamp()
                )
                self._num_racers = 0
                self._num_ready = 0
        else:
            await ctx.send('Only members with moderator permissions can create '
                           'races.')

    @commands.command(pass_context=True)
    async def startrace(self, ctx):
        """Starts the race.

        Only mods can run this command. Performs a number of checks to ensure
        the race is set up properly.
        """
        mention_role = '@everyone'
        for role in ctx.message.guild.roles:
            # Mention only racers on start race if such a role exists
            if str(role) == 'racer':
                mention_role = '{}'.format(role.mention)
        if self.is_mod(ctx.author):
            if self._race_started:
                await ctx.send('Race currently started, please end it before '
                               'starting a new one.')
            elif not self._race_created:
                await ctx.send('No race has been created!')
            elif self._num_racers is None or self._num_racers == 0:
                await ctx.send('There are no racers in the race!')
            elif self._num_ready is None or self._num_ready == 0:
                await ctx.send('There is no one ready in the race!')
            elif self._num_racers != self._num_ready:
                await ctx.send('Not everyone is ready yet!')
            elif self._race_goal is None:
                await ctx.send('Race goal is not set yet!')
            elif self._race_game is None:
                await ctx.send('Race game is not set yet!')
            else:
                await ctx.send('Starting race...')
                await asyncio.sleep(1)
                await ctx.send('5')
                await asyncio.sleep(1)
                await ctx.send('4')
                await asyncio.sleep(1)
                await ctx.send('3')
                await asyncio.sleep(1)
                await ctx.send('2')
                await asyncio.sleep(1)
                await ctx.send('1')
                await asyncio.sleep(1)
                await ctx.send('{}, start!'.format(mention_role))

                self._time_started = datetime.utcnow()
                self._race_started = True

                for racer in self._racer_dict:
                    self._racer_start_times_dict[racer] = self._time_started

                race_start_file_name = 'raceStartTime_{}.txt'.format(
                    self._time_created.timestamp()
                )
                with open(race_start_file_name, 'w+') as race_start_time_file:
                    race_start_time_file.write('Race time: {}\n'.format(
                        self._time_started
                    ))
                    race_start_time_file.close()

                self._num_finished = 0
        else:
            await ctx.send('Only members with moderator permissions can start '
                           'races.')

    @commands.command(pass_context=True)
    async def endrace(self, ctx):
        """Ends the race.

        Only mods can run this command. Outputs results if the race has already
        started, and the results had not been already printed automatically
        when all players completed the race. If the results changed after
        all players completed the race (for instance, a comment was added),
        this will also print out the results.
        """
        if self.is_mod(ctx.author):
            if not self._race_created:
                await ctx.send('No race has been created!')
            else:
                await ctx.send('The race has ended!')
                if self._race_started and not self._results_printed:
                    await self.output_results(ctx, True)

                self._race_created = False
                self._time_created = None
                self._race_started = False
                self._time_started = None
                self._racer_dict = {}
                self._racer_comments_dict = {}
                self._racer_start_times_dict = {}
                self._racer_ready_dict = {}
                self._race_goal = None
                self._race_game = None
                self._race_file_name = None
                self._num_racers = None
                self._num_ready = None
        else:
            await ctx.send('Only members with moderator permissions can end '
                           'races.')

    @commands.command(pass_context=True)
    async def setgoal(self, ctx, *, _goal: str):
        """Sets the goal for the race.

        Only mods can run this command.
        """
        if self.is_mod(ctx.author):
            if self._race_created:
                self._race_goal = _goal
                await ctx.send('Goal set.')
            else:
                await ctx.send('No race currently created!')
        else:
            await ctx.send('Only members with moderator permissions can set '
                           'goals for races.')

    @commands.command(pass_context=True)
    async def goal(self, ctx):
        """Returns the goal for the race."""
        if self._race_created:
            await ctx.send('Race goal: {}'.format(self._race_goal))
        else:
            await ctx.send('No race currently created!')

    @commands.command(pass_context=True)
    async def setgame(self, ctx, *, _game: str):
        """Sets the game for the race.

        Only mods can run this command.
        """
        if self.is_mod(ctx.author):
            if self._race_created:
                self._race_game = _game
                await ctx.send('Game set.')
            else:
                await ctx.send('No race currently created!')
        else:
            await ctx.send('Only members with moderator permissions can set '
                           'games for races.')

    @commands.command(pass_context=True)
    async def game(self, ctx):
        """Returns the game for the race."""
        if self._race_created:
            await ctx.send('Race game: {}'.format(self._race_game))
        else:
            await ctx.send('No race currently created!')

    @commands.command(pass_context=True)
    async def join(self, ctx):
        """Joins the race.

        Only possible if race is created. If the race has already started,
        the player start time that is set is the join time not the general
        start time.
        """
        racer = ctx.author
        if self._race_created:
            if racer in self._racer_dict:
                await ctx.send('<@{}>, you already joined the race!'.format(
                    racer.id
                ))
            else:
                if self._race_started:
                    new_time_started = datetime.utcnow()
                    self._racer_start_times_dict[racer] = new_time_started
                    self._racer_ready_dict[racer] = None
                    self._num_ready += 1
                self._racer_dict[racer] = None
                self._num_racers += 1
                await ctx.send('{} has joined the race!'.format(
                    self.trim_member_name('{}'.format(racer))
                ))
        else:
            await ctx.send('No race currently created!')

    @commands.command(pass_context=True)
    async def unjoin(self, ctx):
        """Unjoins the race.

        Only possible if race is not running.
        """
        racer = ctx.author
        if self._race_started:
            await ctx.send("<@{}>, you can't !unjoin a race that is "
                          "running.".format(racer.id))
            await ctx.send('Please !quit the race instead.')
        elif self._race_created:
            if racer in self._racer_dict:
                self._racer_dict.pop(racer, None)
                self._num_racers -= 1
                if racer in self._racer_ready_dict:
                    self._racer_ready_dict.pop(racer, None)
                    self._num_ready -= 1
                await ctx.send('{} has left the race!'.format(
                    self.trim_member_name('{}'.format(racer))
                ))
            else:
                await ctx.send("<@{}>, you can't leave a race you didn't "
                               "join.".format(racer.id))
        else:
            await ctx.send('No race currently running!')

    @commands.command(pass_context=True)
    async def ready(self, ctx):
        """Readies up for the race.

        Only possible if race is created and not running, otherwise ready
        command is not needed.
        """
        racer = ctx.author
        if self._race_started:
            if racer in self._racer_ready_dict:
                await ctx.send('<@{}>, you already set yourself as '
                               'ready!'.format(racer.id))
            else:
                await ctx.send("You don't need to !ready after the race has "
                               "started.")
                if racer not in self._racer_dict:
                    await ctx.send("Feel free to join the currently running "
                                   "race! Don't worry, your timer will be "
                                   "started from whenever you send the !join "
                                   "command.")
        elif self._race_created:
            if racer in self._racer_dict:
                if racer in self._racer_ready_dict:
                    await ctx.send('<@{}>, you already set yourself as '
                                   'ready!'.format(racer.id))
                else:
                    self._racer_ready_dict[racer] = None
                    self._num_ready += 1
                    await ctx.send('{} is ready!'.format(
                        self.trim_member_name('{}'.format(racer))
                    ))
            else:
                await ctx.send('<@{}>, please join the race before setting '
                               'yourself as ready.'.format(racer.id))
        else:
            await ctx.send('No race currently created!')

    @commands.command(pass_context=True)
    async def unready(self, ctx):
        """Unreadies for the race.

        Only possible if race is created and not started.
        """
        racer = ctx.author
        if self._race_started:
            await ctx.send("<@{}>, the race is already running, it's a bit too "
                           "late to unready.".format(racer.id))
        elif self._race_created:
            if racer in self._racer_dict:
                if racer in self._racer_ready_dict:
                    self._racer_ready_dict.pop(racer, None)
                    self._num_ready -= 1
                    await ctx.send('{} is no longer ready!'.format(
                        self.trim_member_name('{}'.format(racer))
                    ))
                else:
                    await ctx.send('<@{}>, you did not set yourself as ready '
                                   'yet!'.format(racer.id))
            else:
                await ctx.send('<@{}>, you did not join the race yet.'.format(
                    racer.id
                ))
        else:
            await ctx.send('No race currently created!')

    @commands.command(pass_context=True)
    async def quit(self, ctx):
        """Quits the race.

        Only possible if race is created.

        If race is started: player status is set to forfeited, and if all
        racers have completed the race, the results are output. If racer has
        already !done the race, this does not change the status.

        If race is created, behaves the same as unjoin.
        """
        racer = ctx.author
        if self._race_started:
            if racer in self._racer_dict:
                if self._racer_dict[racer] is None:
                    self._racer_dict[racer] = 'Forfeited'
                    self._racer_comments_dict[racer] = ''
                    await ctx.send('{} has quit the race!'.format(
                        self.trim_member_name('{}'.format(racer))
                    ))

                    self._num_finished += 1
                    if self._num_finished == self._num_racers:
                        await ctx.send('Everyone has completed the race!')
                        await self.output_results(ctx, True)
                        self._results_printed = True
                elif self._racer_dict[racer] == 'Forfeited':
                    await ctx.send('<@{}>, you already quit the race.'.format(
                        racer.id
                    ))
                else:
                    await ctx.send('<@{}>, you have already completed the '
                                   'race.'.format(racer.id))
                    await ctx.send('Please !undone if you want to undo your '
                                   'previous race completion.')
            else:
                await ctx.send("<@{}>, you didn't join the race.".format(
                    racer.id
                ))
        elif self._race_created:
            if racer in self._racer_dict:
                self._racer_dict.pop(racer, None)
                self._num_racers -= 1
                if racer in self._racer_ready_dict:
                    self._racer_ready_dict.pop(racer, None)
                    self._num_ready -= 1
                await ctx.send('{} has left the race!'.format(
                    self.trim_member_name('{}'.format(racer))
                ))
            else:
                await ctx.send("<@{}>, you can't leave a race you didn't "
                               "join.".format(racer.id))
        else:
            await ctx.send('No race has been created!')

    @commands.command(pass_context=True)
    async def unquit(self, ctx):
        """Unquits the race.

        Only possible if race is started and the racer has previously quit the
        race.
        """
        racer = ctx.author
        if self._race_started:
            if racer in self._racer_dict:
                if self._racer_dict[racer] is None:
                    await ctx.send('<@{}>, you have not completed the race '
                                   'yet.'.format(racer.id))
                elif self._racer_dict[racer] != 'Forfeited':
                    await ctx.send('<@{}>, you never quit the race.'.format(
                        racer.id
                    ))
                else:
                    self._racer_dict[racer] = None
                    self._num_finished -= 1
                    self._results_printed = False
                    await ctx.send('{} is back in the race!'.format(
                        self.trim_member_name('{}'.format(racer))
                    ))
            else:
                await ctx.send("<@{}>, you didn't join the race.".format(
                    racer.id
                ))
        else:
            await ctx.send('No race currently running!')

    @commands.command(pass_context=True)
    async def done(self, ctx):
        """Finishes the race.

        Only possible if race is started, keeps track of done time. If the
        racer has previously completed the race, this does not change the
        previous results.

        Outputs results if everyone has completed the race.
        """
        racer = ctx.author
        if self._race_started:
            if racer in self._racer_dict:
                if self._racer_dict[racer] is None:
                    finish_time = datetime.utcnow()
                    racer_start_time = self._racer_start_times_dict[racer]
                    time_taken = finish_time - racer_start_time
                    finish_msg = '{racer} has finished the race in {time}!'
                    await ctx.send(finish_msg.format(
                        racer=self.trim_member_name('{}'.format(racer)),
                        time=self.round_time(time_taken)
                    ))

                    self._racer_dict[racer] = str(time_taken)
                    self._racer_comments_dict[racer] = ''
                    self._num_finished += 1
                    if self._num_finished == self._num_racers:
                        await ctx.send('Everyone has completed the race!')
                        await self.output_results(ctx, True)
                        self._results_printed = True
                elif self._racer_dict[racer] == 'Forfeited':
                    await ctx.send('<@{}>, you have already left the '
                                   'race.'.format(racer.id))
                    await ctx.send('Please !undone or !unquit if you want to '
                                   'rejoin the race.')
                else:
                    await ctx.send('<@{}>, you have already completed the '
                                   'race.'.format(racer.id))
                    await ctx.send('Please !undone if you want to undo your '
                                   'previous race completion.')
            else:
                await ctx.send("<@{}>, you didn't join the "
                               "race.".format(racer.id))
        else:
            await ctx.send('No race currently running!')

    @commands.command(pass_context=True)
    async def undone(self, ctx):
        """Undoes the race.

        Only possible if race is started. If the racer has previously quit
        the race, this behaves equivalently to unquit.
        """
        racer = ctx.author
        if self._race_started:
            if racer in self._racer_dict:
                if self._racer_dict[racer] is None:
                    await ctx.send('<@{}>, you have not completed the race '
                                   'yet.'.format(racer.id))
                else:
                    self._racer_dict[racer] = None
                    self._num_finished -= 1
                    self._results_printed = False
                    await ctx.send('{} is back in the race!'.format(
                        self.trim_member_name('{}'.format(racer))
                    ))
        else:
            await ctx.send('No race currently running!')

    @commands.command(pass_context=True)
    async def comment(self, ctx, *, comment_string: str):
        """Comments on the race.

        Only possible if race is started. Comments are only accepted if a
        person had finished or forfeited a race.
        """
        racer = ctx.author
        if self._race_started:
            if racer in self._racer_dict:
                if self._racer_dict[racer] is None:
                    await ctx.send("<@{}>, you didn't complete the race "
                                   "yet.".format(racer.id))
                    await ctx.send('Either !done if you finished or !quit if '
                                   'you wish to forfeit before commenting.')
                else:
                    self._racer_comments_dict[racer] = comment_string
                    self._results_printed = False
            else:
                await ctx.send("<@{}>, you didn't join the race.".format(
                    racer.id
                ))
        else:
            await ctx.send('No race currently running!')

    @commands.command(pass_context=True)
    async def time(self, ctx):
        """Returns the current running time of the race.

        Only possible if race is started.
        """
        if self._race_started:
            current_time = datetime.utcnow()
            time_taken = current_time - self._time_started
            await ctx.send('Race has been running for {}'.format(
                self.round_time(time_taken)
            ))
        else:
            await ctx.send('No race currently running!')

    @commands.command(pass_context=True)
    async def entrants(self, ctx):
        """Returns the current list of entrants of the race.

        Only possible if race has been started. Does not mention the players.
        """
        if self._race_created:
            racer_list = 'Race entrants:\n'
            for racer in self._racer_dict:
                ready_status = ''
                if racer in self._racer_ready_dict:
                    ready_status = ' (ready)'
                racer_list = '{prev_racers} {racer}{status}\n'.format(
                    prev_racers=racer_list,
                    racer=self.trim_member_name('{}'.format(racer)),
                    status=ready_status
                )
            if racer_list == 'Race entrants:\n':
                racer_list = 'No entrants yet!'

            await ctx.send(racer_list)
        else:
            await ctx.send('No race currently running!')

    @commands.command(pass_context=True)
    async def results(self, ctx):
        """Returns the current results of the race.

        Only possible if race is created.
        """
        if self._race_started:
            await self.output_results(ctx, False)
        else:
            if self._race_created:
                await ctx.send('No race has been started!')
            else:
                await ctx.send('No race has been created!')

    @commands.command(pass_context=True)
    async def download(self, ctx):
        """Test downloading all relevant pack info"""
        all_info = {'attachments': []}
        print(ctx.message.channel)
        async for msg in ctx.message.channel.history(limit=10000):
            if msg.attachments:
                for attachment in msg.attachments:
                    all_info['attachments'].append({
                        'attach_name': attachment.filename,
                        'attach_url': attachment.url,
                        'time': msg.created_at.strftime('%Y-%m-%d %H:%M:%S') + ' -0000',
                        'author': msg.author.name
                    })
        with open('demopack_download.yaml', 'w') as out_stream:
            yaml.dump(all_info, out_stream)

    async def output_results(self, ctx, mention_players):
        """Outputs the results from the race

        Results format: 1. racerName racerTime racerComments
        racerTime can also be 'Forfeited' if the racer did not finish the race.
        racerTime and racerComments can be empty if the racer did not set an
        end status on the race. Also outputs results in the same format to a
        textfile in comma-delimited rows (with the comments on new lines).
        """
        racer_not_finished = {}
        racer_forfeited_dict = {}
        racer_done_dict = {}
        for racer in self._racer_dict:
            if self._racer_dict[racer] is None:
                racer_not_finished[racer] = ''
            elif self._racer_dict[racer] == 'Forfeited':
                racer_forfeited_dict[racer] = 'Forfeited'
            else:
                racer_done_dict[racer] = self._racer_dict[racer]

        sorted_racer_done = sorted(racer_done_dict.items(),
                                   key=operator.itemgetter(1))

        results_string = ''
        file_string = ''
        index = 1
        for racer_tuple in sorted_racer_done:
            racer_time = self.round_time(racer_tuple[1])
            results_string, file_string = self.format_results(
                results_string,
                file_string,
                racer_tuple[0],
                racer_time,
                index,
                mention_players
            )
            index += 1
        for racer in racer_forfeited_dict:
            results_string, file_string = self.format_results(
                results_string,
                file_string,
                racer,
                'Forfeited',
                index,
                mention_players
            )
            index += 1
        for racer in racer_not_finished:
            if mention_players:
                racer_name = '<@{}>'.format(racer.id)
            else:
                racer_name = self.trim_member_name('{}'.format(racer))
            results_string = self.RESULT_LINE_NO_FINISH_TEMPLATE.format(
                prev_results=results_string,
                idx=index,
                racer=racer_name
            )
            file_string = self.RESULT_FILE_LINE_NO_FINISH_TEMPLATE.format(
                prev_results=file_string,
                idx=index,
                racer=racer_name
            )
            index += 1

        output = '{}{}\n{}{}\n{}\n{}'.format(
            'Race game: ',
            self._race_game,
            'Race goal: ',
            self._race_goal,
            'Race results:',
            results_string
        )

        if results_string:
            await ctx.send(output)
        if file_string:
            with io.open(self._race_file_name, 'w+', encoding='utf8') as \
                    race_file:
                race_file.write(file_string)
                race_file.close()

    @staticmethod
    def trim_member_name(member_name):
        """Trims member name

        Gets rid of the #xxx string at the end of the player name.
        """
        return member_name.split('#')[0]

    @staticmethod
    def round_time(time_to_round):
        """Rounds duration time down to the second"""
        return str(time_to_round).split('.')[0]

    @staticmethod
    def is_mod(member):
        """Checks if a member has a mod role.

        Mod roles hardcoded to match #doom mod roles (race mod)
        """
        for role in member.roles:
            if role.name.lower() == 'race mod':
                return True

        return False

    def format_results(self, results_string, file_string, racer, time, index,
                       mention_players):
        """Formats results for players who are set as done or forfeited"""
        if mention_players:
            racer_name = '<@{}>'.format(racer.id)
        else:
            racer_name = self.trim_member_name('{}'.format(racer))
        racer_comments = self._racer_comments_dict[racer]
        results_string = self.RESULT_LINE_TEMPLATE.format(
            prev_results=results_string,
            idx=index,
            racer=racer_name,
            time=time,
            comments=racer_comments
        )
        file_string = self.RESULT_FILE_LINE_TEMPLATE.format(
            prev_results=file_string,
            idx=index,
            racer=racer_name,
            time=time,
            comments=racer_comments
        )

        return results_string, file_string


PREFIXES = ['!', '\N{HEAVY EXCLAMATION MARK SYMBOL}']
DESCRIPTION = '''Bot for racing and keeping track of race results'''
bot = commands.Bot(command_prefix=PREFIXES, description=DESCRIPTION)


@bot.event
async def on_ready():
    """Prints debug info on startup."""
    print('------')
    print('Username: ' + bot.user.name)
    print('User ID: {}'.format(bot.user.id))
    print('------')


@bot.event
async def on_resumed():
    """Triggered when bot resumes after interruption"""
    print('Resumed...')


@bot.event
async def on_command_error(error, ctx):
    """Catches errors and sends messages to channel."""
    if isinstance(error, commands.MissingRequiredArgument):
        await bot.send_message(ctx.message.channel,
                               'Missing required argument for command.')


if __name__ == '__main__':
    with open('token.txt') as token_file:
        token = token_file.readline()
    bot.add_cog(Race(bot))
    bot.run(token.rstrip())
