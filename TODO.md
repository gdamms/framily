# TODO

- [ ] after doing an action, refetch the needed data to update the ui (like after adding a picture, refetch the pictures list, after adding a framily, refetch the framilies list, ...)
- [ ] make the frame in deep sleep when not fetching images (to reduce power consumption) make it wake up when the next fetch is due, and go back to deep sleep after fetching the image and displaying it. make this feature optional in the frame settings (default to enabled)
- [ ] progressive web app
  - [ ] include frame initialization in the pwa - seemless experience for the user, only in the app: manage the wifi-hotspot, web interface adapted, ...
- [ ] when overviewing a picture, allow the user to draw a "focus area" on the picture: a rectangle (clamp to picture size) will be used to crop the picuture to the focus area (helps to manage horizontal pictures on vertical frames - and visversa). when croping, picture should be ALWAYS contain the focus area, if needed, add black bars to the picture. do not restric the size to the focus area, the crop should cover as much as possible of the picture while keeping the focus area in it
- [ ] add more data to the frame status endpoint (wifi strength, software version, ...) and hide some to the non-admin users (like the wifi strength, ip address, ...) concider non-admin users as external users that have nothing to know about tecnical details of the frame
- [ ] disablable user registration (no idea what would be the good way to do this... should frames allow to create?)
- [ ] add a way to manage framily random picture picking (rolling, random, queue, most recent more often, ...)
- [ ] public invite link to join a framily, an identified user that use this link will be added to the framily (the link should be unique to the framily, revokable and if remake, the old link should not work anymore)

## Done

- [x] move the user settings to a burger on the top right: profile, settings, theme, logout (remove the settings tab from the user profile page)
- [x] in the settings page: change display name (even if can be change clicking on the name in the profile page), change password, change password, change theme (even if can be change clicking on the theme switch in the top right dropdown), delete account (danger zone)
- [x] add a dark/light mode switch (default to light mode)
- [x] when uploading an avatar (framily or user), open a popup to crop the image to a square (with a cirlce indicator to show what will be the final avatar) and resize it to 256x256 before sending it to the server
- [x] add descriptions to pictures (like a caption, with limited length) and display them on the frame (activable in the frame settings, default to enabled) DONT DISPLAY NO CAPTION IF NO CAPTION IS SET - might lead to a adaptation of the current Uploader name and date overlay that are displayed
- [x] enhance picture overview: (bug: when closing gets back to the dashboard, use popup instead) add caption section
- [x] enhance the ui (probably done by myself as I have a better idea of what I want)
- [x] change role integer to enum string in database and code
- [x] when the frame fetches a picture, it should be sent read to be displayed - the frame does not manage image rotation, croping, or resizin, it should only get the image and display it as is (with some security checks, like checking the image size and type) with it, it receive the next delay before fetching the next image
- [x] add settings to the framily:
  - [x] add a setting to change the frame's display interval (in minutes)
  - [x] add a setting to change the frame's orientation (4 directions)
- [x] remove settings tab from users profiles that are not me
- [x] next to my display name, in my profile, it should have a little pen icon. When I click on the pen/name, it should start editing it. When I click outside of the input or press enter, it should save my user display name.
- [x] remove the "add framily" button in the bottom navbar and add a "add framily" button in the top like the "invite user" button when in members tab of a framily. DO the same for add picture button in the pictures tab of a framily, in my profile pictures page and in the dashboard. In the dashboard and in my profile pictures page, all framilies should be checked by default. But when in a framily, only that framily should be checked by default.
- [x] just like user can rename their display name, admins can rename the framily name. an icon next to the framily name should allow admins to edit the framily name when clicking on it. When the input loses focus or enter is pressed, it should save the new framily name. It can also be changed in the framily settings tab.
- [x] in the frame settings display the frame ip address, the frame should send its ip address on the wifi network using the status endpoint (allows to access the frame webinterface)
- [x] the frame should send status periodically to the server (every fetch like the settings?) no only once at startup
- [x] frame settings endpoint should not only return the next delay (maybe there is nothing else for now, might have changed) but a json with multiple settings (that contain the next delay) changes need to be done server side and frame side
- [x] as the frame is eink spectra6, a preprocessing should be apply to better display the images (contrast, brightness, etc...) a very adaptative preprocessing should be applied and configurable in the frame settings (one simple cursor in the settings to change the preprocess level, abstract to users), the real work is "how to preprocess the image". Sill have to be done server side
- [x] when someone leaves a framily, all picture visibility between the user pictures and the framily should be removed (the user pictures should not be deleted, but the visibility to the framily should be removed)
- [x] group frame status like ip and resolution in a section at the end of the frame settings page
- [x] add a danger zone in the framily settings page to delete the framily (when trying to leave a framily while beeing the last admin, it is not possible, send a message to the user to delete the framily instead as they are the last admin)
- [x] add a danger zone in the user settings page to delete the user account
- [x] put settings into separate sections for the framily and the user settings pages
- [x] make user authentication longer (infinite, unless they untick the "stay logged in" when loging)
- [x] when the frame faces a 404 wrong framily token or id, the webinterface should display a message to tell that the framily might have been deleted so you might wanna reset recreate the framily. change how the frame reset works, it should not reset the wifi, password or url, but the id and auth token, recreate a new framily as if it was it first initialization. Plus, when clicking on reset, first send the server reponse (like when saving), then do what has to be done
