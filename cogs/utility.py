import discord
from discord.ext import commands
from discord.ext.commands import Context
import requests

# Create embeds for weather command


def weather_embed(data):
    city_name = data['city']['name']
    country = data['city']['country']
    lat = data['city']['coord']['lat']
    lon = data['city']['coord']['lon']
    forecast_list = data['list']

    # Create the embed
    embed = discord.Embed(
        title=f"Weather Forecast for {city_name}, {country}",
        description=f"Location: {lat}, {lon}",
        color=discord.Color.blue()
    )

    embed.set_thumbnail(url=data['city']['url'])  # City image from response

    # Add summary information (first entry only for brevity)
    entry = forecast_list[0]
    temp = entry['main']['temp'] - 273.15  # Convert from Kelvin to Celsius
    feels_like = entry['main']['feels_like'] - 273.15
    description = entry['weather'][0]['description'].capitalize()
    wind_speed = entry['wind']['speed']
    humidity = entry['main']['humidity']

    embed.add_field(
        name=f"📅 {entry['dt_txt']}",
        value=(
            f"🌡️ Temp: {temp:.2f}°C (Feels like {feels_like:.2f}°C)\n"
            f"☁️ {description}\n"
            f"💨 Wind: {wind_speed} m/s | 💧 Humidity: {humidity}%"
        ),
        inline=False
    )

    # Add only the next two entries (simplified)
    for entry in forecast_list[1:3]:
        dt = entry['dt_txt']
        temp = entry['main']['temp'] - 273.15
        description = entry['weather'][0]['description'].capitalize()

        embed.add_field(
            name=f"📅 {dt}",
            value=(
                f"🌡️ Temp: {temp:.2f}°C\n"
                f"☁️ {description}"
            ),
            inline=False
        )

    embed.set_footer(text="Weather data provided by RapidAPI")

    return embed
    

# Here we name the cog and create a new class for the cog.


class Utility(commands.Cog, name="utility"):
    def __init__(self, bot) -> None:
        self.bot = bot
        
    @commands.hybrid_command(
        name="help", description="List all commands the bot has loaded."
    )
    async def help(self, context: Context) -> None:
        prefix = self.bot.config["prefix"]
        embed = discord.Embed(
            title="Help", description="List of available commands:", color=0xBEBEFE
        )
        for i in self.bot.cogs:
            if i == "owner" and not (await self.bot.is_owner(context.author)):
                continue
            cog = self.bot.get_cog(i.lower())
            commands = cog.get_commands()
            data = []
            for command in commands:
                description = command.description.partition("\n")[0]
                data.append(f"{prefix}{command.name} - {description}")
            help_text = "\n".join(data)
            embed.add_field(
                name=i.capitalize(), value=f"```{help_text}```", inline=False
            )
        await context.send(embed=embed)


    @commands.hybrid_command(
        name="translate",
        description="Translate a text from English to Vietnamese.",
    )
    async def translate(self, context: Context, *,  text: str) -> None:
        """
        Translate a text from English to Vietnamese.

        :param context: The hybrid command context.
        :param text: The text to translate.
        """
        url = "https://google-translator9.p.rapidapi.com/v2"
        querystring = {"q": text, "target": "vi",
                       "source": "en", "format": "text"}

        headers = {
            "X-RapidAPI-Key": "4e43b4c3bcmsh1827e6c7fea3df3p1ed847jsnf9e4737a2128",
            "X-RapidAPI-Host": "google-translator9.p.rapidapi.com",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=querystring, headers=headers)
        if response.status_code == 200:
            json_response = response.json()
            if "data" in json_response:
                translated_text = json_response["data"]["translations"][0]["translatedText"]
                await context.send(translated_text)
            else:
                await context.send("Error: 'data' key not found in the response.")
        else:
            await context.send(f"Error: {response.status_code}")

    @commands.hybrid_command(
        name="weather",
        description="Get the weather of a city."
    )
    async def weather(self, context: Context, *, city: str) -> None:
        """
        Get the weather of a city.

        :param context: The hybrid command context.
        :param weather: The name of city to get the weather.
        """
        url = "https://weather-api167.p.rapidapi.com/api/weather/forecast"
        querystring = {"place": city}

        headers = {
            "x-rapidapi-key": "4e43b4c3bcmsh1827e6c7fea3df3p1ed847jsnf9e4737a2128",
            "x-rapidapi-host": "weather-api167.p.rapidapi.com",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            json_response = response.json()
            embed = weather_embed(json_response)
            await context.send(embed=embed)
        else:
            await context.send(f"Error: {response.status_code}")

    @commands.hybrid_command(
        name="wiki",
        description="Search information on Wikipedia."
    )
    async def wiki(self, context: Context, *, query: str) -> None:
        """
        Search information on Wikipedia.

        :param context: The hybrid command context.
        :param query: The query to search on Wikipedia.
        """
        url = "https://wikipedia-api1.p.rapidapi.com/get_summary"
        querystring = {"q": query, "lang": "vi", "sentences": "3"}

        headers = {
            "x-rapidapi-key": "4e43b4c3bcmsh1827e6c7fea3df3p1ed847jsnf9e4737a2128",
            "x-rapidapi-host": "wikipedia-api1.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            json_response = response.json()
            await context.send(json_response['data'])
        else:
            await context.send(f"Lỗi khi tìm kiếm thông tin.")           

# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.

async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))
