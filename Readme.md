#Vanilla Forums Integration for Coursebuilder

This plugin for [Google Coursebuilder](https://code.google.com/p/course-builder/) enables integration between Google Coursebuilder and [Vanilla Forums](http://vanillaforums.org/).  This is compatible with both the self-hosted and Cloud offerings of Vanilla Forums.  This integration allows much more powerful forum implementations than are available in the existing Coursebuilder install or using Google Forums.

##Coursebuilder Installation
####`modules/vanilla`
Copy this folder into the `modules` directory of your Coursebuilder installation.  No further action is necessary.

###`main.py`
This is the main Python file.  If you've already modified it, add the following lines of code to the main.py file:

```

from modules.vanilla import vanilla
vanilla.register_module().enable()

```
###CSS
Add the following code to your course CSS file:
```
#vanilla-comments iframe{
		width: 1px !important;
        min-width: 100% !important;
        *width: 100% !important;
}
```

####`views/`
These files will overwrite the existing views in your Coursebuilder install.  Any customizations made to the released versions of these views will need to be recreated.  These new views add the following functionality to Coursebuilder:

| Page Title             | Description of Modifications                                                                              |
| ---------------------- | --------------------------------------------------------------------------------------------------------- |
| `forum.html`           | Replaces embedded Google Forum with an embedded Vanilla Forum at the root of the forum structure.         |
| `student_profile.html` | Adds an embedded instance of Vanilla Forums at the forums profile screen.                                 |
| `base_course.html`     | Modifies the base course template to hide the Forums link if the viewer isn't registered for the course.  |  

##Vanilla Forums Setup
You must install the [JS Connect Plugin for Vanilla](http://vanillaforums.org/addon/jsconnect-plugin) in your Vanilla instance prior to beginning.  Generate a new Client ID and Secret for Vanilla using the plugin dashboard.  Use your course URL for the **Sign In Url** and the **Register Url** fields.  For the Authenticate URL, use `[course_url]/vanilla_auth.json`.

**NOTE**: If you are using the Cloud-hosted version of the Vanilla Forums, users will need to click the "Sign-In" link at all of the forum pages in order to access forum content.  For the self-hosted version, the [Vanilla jsConnect Auto SignIn 0.1.8b Plugin](http://vanillaforums.org/addon/jsconnectautosignin-plugin) can be used to make this implementation nearly transparent.

In the Vanilla Forums Dashboard, click on the `Embed Forum` link in the sidebar, and click `Enable Embedding`.

##Coursebuilder Setup
Once you've created your Client ID and secrets, note these for use in Coursebuilder.  In the Coursebuilder Dashboard, click `Settings` and `Advanced Edit`.  In the `course.yaml` file, add the following three lines under `course:`

```

  VANILLA_EMBED_URL: [URL to your Vanilla Forums.  It's not necessary to include http:// or https://]
  VANILLA_CLIENT_ID: '[client id from Vanilla Forums dashboard]'
  VANILLA_SECRET_KEY: [secret key from your Vanilla Forums dashboard]

```

Once you're registered, test your install, you should be good to go!

##Including Forum Categories in Lessons
You can include an embedded forum at the category level in a lesson. In the Rich Text editor at the lesson level, click on the Toolbox.  Under `Category ID:` enter the URL slug for the Vanilla category you want to use (this will appear when you create the Category in Vanilla). 


##Registration
If a user who is not registered attempts to access the forums, Appengine will throw a 500 error.  Therefore, the Profile and Forums links are hidden in the revised template if a student isn't registered.

##Security and SSL
Both the Vanilla Forums instance and the Google Coursebuilder instance should make use of SSL.  This is just good practice.  Embedding of forums and cross-site signin will fail if the same SSL certificate and base domain names isn't in use for both the Vanilla instance and the Coursebuilder install in Google App Engine.
