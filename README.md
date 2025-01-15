# BountyChecker
A tool to check Cetus Bounties in Real Time

# How does this work?
It reads and parses your EE.log

# Will I get banned for this?
Short Answer is: no.
Long Answer is: The Scripts parse EE.log, the logfile where Warframe logs all sorts of stuff, also bounty stages. A lot of 3rd parts Apps (such as YATE, Alecaframe and PTAnalyzer) use this to work. So far I am not aware of anyone being banned, but use at your own risk as any other program. 

# It shows up as a Virus?!?
Unfortunately, this is how it currently is. The source code is freely avaible here though and you can choose to check it and modify it as you please.

# Why are there two versions?
One version (with_share) sends good bounties to us. That way everyone can benefit from good bounties. The other version does not - choose whichever you like (though ofc we hope for people actively sharing their bounties). 

# What does "with_share" / "no_share" mean?
As mentioned above, there are two versions of the program. One named "with_share", one named "no_share". 

The functionality of both versions is the exact same for your end. You yourself will have no advantages or disadvantages running either version.

**SHARE**

This version will send us information about a good bounty (see below chapter on what it sends). That way, other people can see whenever a good bounty is up that is not the base quest. Basically you are "sharing" your rolls with everyone.

**NO_SHARE**

This version does not send anything to us. That way, you can still run the bounty but others may not be aware of a good bounty being up.

# What does it send?
It sends some Game Data, thats all. No IP Adress or Username or anything:
```/Lotus/Types/Gameplay/Eidolon/Jobs/SabotageBountySab/Lotus/Types/Gameplay/Eidolon/Jobs/ReclamationBountyCap```
```SolNode228_HUB```
```/Lotus/Types/Game/MissionDecks/EidolonJobMissionRewards/TierETableCRewards ```
```/Lotus/Types/Gameplay/Eidolon/Jobs/ReclamationBountyCap_-4_CetusHub4_65b1683b0000000000000008_TentB```
```['/Lotus/Types/Gameplay/Eidolon/Encounters/DynamicRescue', '/Lotus/Types/Gameplay/Eidolon/Encounters/DynamicAssassinate', '/Lotus/Types/Gameplay/Eidolon/Encounters/HiddenResourceCaches', '/Lotus/Types/Gameplay/Eidolon/Encounters/DynamicHijack', '/Lotus/Types/Gameplay/Eidolon/Encounters/DynamicCapture']```

# How to get the .py working?
Install Python 3.11 (this is what is has been tested on, may work on lower versions too). Then do `py -m pip install -r requirements.txt` in the folder.

# Will this get updates?
Yes

# MacOS?
If you, for whatever godsaken reason play Warframe on MacOS, [RaajYedida made a port of this for MacOS](https://github.com/RaajYedida/WFBountyCheckerMacOS)
