MikuMikuMoving V1.2.9.2
03 Jun 2018

MikuMikuMoving is compaible software with MikuMikuDance.


Requirements
========================================================
Windows Vista or later
.NET Framework 4.0
Microsoft Visual C++ Runtime Components
DirectX 9.0c (2010 Feb or later)

Microsoft .NET Framework 4 (Web Installer)
http://www.microsoft.com/en-us/download/details.aspx?id=17851
Visual C++ Redistributable for Visual Studio 2012 Update 4
http://www.microsoft.com/en-us/download/details.aspx?id=30679
DirectX End-User Runtime Web Installer
http://www.microsoft.com/en-us/download/details.aspx?id=35&


Install/UnInstall
========================================================
You only put the extracted files.
MikuMikuMoving doesn't write into registory.

When you want to uninstall, please delete the folder.

The following files are for configuration.
You can delete the files.

Settings.xml		View settings, Folder settings, etc.
DockLayout.xml		Dock windows layout
CommandBarLayout.xml	Command bar layout


Shortcut keys
========================================================
Ctrl+A		Select all bones and all keyframes
Shift+A		Select all bones

Ctrl+.		Next Bookmark
Ctrl+,		Previous Bookmark
Ctrl+M		Regist Bookmark

Ctrl+C		Copy
Ctrl+X		Cut
Ctrl+V		Paste
Ctrl+W		Reverse paste
Delete		Delete

C		Toggle bone marker display
D		Apply bias to center
E		Initialize pose
G		Switch between global and local modes
I		Insert frame column
K		Delete frame column
P		Play/Stop
S		Select unregistered bones
V		Translucently
W		Reverse pose
X		Show/Hide Pose handle
Z		Toggle camera keyframe enable
Enter		Regist keyframe
Tab			Toggle model/accessory/camera
Shift+Tab	Toggle model/accessory/camera (recursive)

Home	Move zero frame
End		Select Project property (Camera Mode Only)
↑,↓	Move row
→		Move 1 frame forward
←		Move 1 frame back
Ctrl+→		Move to the next keyframe
Ctrl+←		Move to the previous keyframe

.			X rotation
/			Y rotation
\			Z rotation
;			X move
:			Y move
]			Z move

Ctrl+S		Save project
Ctrl+Z		Undo
Ctrl+Y		Redo

F1			Right side view
Shift+F1	Left side view
F2			Top view
Shift+F2	Bottom view
F3			Frontal view
Shift+F3	Rear view

Shift+F8	Healing function (when model is selected)


Disclaimer
==============================================================================
In no event shall the author of this Software be liable for any damages arising out of the use of or inability to use the product.

You need not to apply for permission for publish the images, movies, files(MPJ,VMD,MVD,etc) output from MikuMikuMoving.
But the author is not liable for any problem.
Please note the copyrights for music, image, movei, character, etc.


Contact
========================================================
mogg.dx@gmail.com


History
============================================================
03 Jun 2018	V1.2.9.2
			Revice about IK
			Fix some bugs
02 Jun 2018	V1.2.9.1
			Revise not effecting center bias moving on v1.2.9.0
			Revice "after physics" bone on v1.2.9.0
			Revice local inhere bone on v1.2.9.0
			Revice IK on v1.2.9.0
			Fix some bugs.
26 May 2018	V1.2.9.0
			Revice IK and inhere bone caluculations.
			Fix: can not loading movie for Windows10 x64.
			Add InsertColumn method for Plugin Model/Effect/Accessory/Camera/Light.
24 Apr 2018	V1.2.8.5
			Add bone and morph smoothing function by right clicking bone/morph title on sequence.
			"Paste other bone" can morph not only bone.
			Fix: morph keyframes are disappeared when undo.
20 Apr 2018	V1.2.8.4
			Revise Pserception Neuron function.
15 Apr 2018	V1.2.8.2
			Revise Pserception Neuron function.
			Fix stopping to output video on Windows 10.
03 Apr 2018	V1.2.8.0
			Support Perception Neuron.
12 Aug 2017	V1.2.7.5
			Improve performance for rotate scene.
			Fix:property of model or camera is not changed correctly.
			Fix:Toon color is not readed correctly when the texture format is special(DDS etc).
04 Aug 2017	V1.2.7.4
			Add "Don't move mouse pointer" option on settings. The mouse pointer do not move when dragging on bone rotate/move or camera zoom/move controls.
			Improve changing accessory selection.
			Improve range bone selection.
			Improve extended bone handle.
			Fix some bugs.
17 Jun 2017	V1.2.7.3
			Fix:Motion clip effects before the start position.
			Fix:MMM freeze when the specific model.
			Fix:Default camera can be deleted.
			Fix:Changed name of model is not shown in Rendering Order and Related Order dialog.
			Fix:An error occurs when minimize the window using captions.
			Fix:An error occurs when using audio fade-in or fade-out.
			Fix:Outputting movie stops when using filter.
			Fix some bugs.
28 Sep 2015	V1.2.7.2
			Can move timeline with middle mouse button drag on timeline.
			Enable keyboard shortcut Move/Rotate operation with Accessory and Effect object.
			Can move previous/Next keyframe using Back/Next button with 5 button mouse.
			Fix the behavior using Alt + mouse wheel on timeline.
			Fix a morph value of child motion clip is set on Parent motion-clip.
			Fix a motion clip start position is minus when loading the motion clip.
			Fix can not motion-blend when the huge frame position.
			Fix some bugs.
21 Sep 2015	V1.2.7.1
			Can save the motion clip on/off.
			Can load Vocaloid4 vsqx file.
			Fix some bugs.
23 Aug 2015	V1.2.7.0
			Fix moving 2 frames by using allow keys.
			Fix selecting camera is very slow.
			Add "Deselect track when click empty" option.
			 - The bone track is still selected or deselected when click empty.
			Add spineditor for morph.
			Add zero-button for bone move/rotation.
			Fix some bugs.
18 Aug 2015	V1.2.6.8
			Update BulletSharp into 2.83
			Fix: Scale and alpha updown control is strange on Effect object.
			Fix: Do not select bones on Timeline when the bones is selected on screen.
			Can camera rotate and zoom by mouse at same time.
			Fix some bugs.
13 Oct 2014	V1.2.6.7
			Fix skinngin bug.
13 Oct 2014	V1.2.6.6
			[Important] Revice scaling position when model size is changed.
				* The model position is different when load exists project file changed model size.
			Add skins(Mac,lueprint,Dark,Metropolis Dark)
			Can move audio minus position.
			Fix changing the audio frequency when audio start position is changed.
			Fix not changed ground shadow deep when loading project file.
			Fix some bugs.
04 Oct 2014	V1.2.6.5
			Don't render when loading project.
			Save effect On/Off flag in setting file.
			Revise Bone.CurrentLocalMotion in Plugin
			Fix some bugs.
15 Sep 2014	V1.2.6.4
			Fix:Not use camera Z-Move control with v1.2.6.3.
15 Sep 2014	V1.2.6.3
			Can rote/move camera by key assign with Camera Mode
			Fix the wrong position when using external bone.
			Fix some bugs.
14 Sep 2014	V1.2.6.2
			Can set XYZ Axis control speed with Settings.
			Fix:An error occurs when loading a project file with external bone.
			Fix:Not effect some external bone with v1.2.6.1
13 Sep 2014	V1.2.6.1
			Add key assigns for bone rotation/move.
			 - Can rotate/move the bone when down the key and move mouse.
			 - Default './\' is rotation, ';:]' is moving.
			 - Not operate when mouse cursor on out of window.
			Fix axis bone is also applicable when the bone is IK link.
			 * Note: Different from MMD
			Fix:Plugin ScreenImage_3D object mouse event.
			Fix some bugs.
03 Aug 2014	V1.2.6.0
			Fix:External related bone and Accessory related bone is not set when load project file created with older v1.2.5.13.
			Fix:an error occurs when set related bone.
			Fix some bugs.
02 Aug 2014	V1.2.5.16
			Can quasi interpolate on External Related bone and Accessory Related bone.
			 - Enable by "Interpolate" checkbox.
			 - Interpolate by target bone "current" position.
			Fix:Curring is remained with some effects.
			Fix some bugs.
01 Aug 2014	V1.2.5.15
			Can On/Off EffectCache with settings.
			Fix:curring do not work on OffscreenTarget.
			Fix:an error occurs when using shared bool variables on effect.
			Fix some bugs.
26 Jul 2014	V1.2.5.14
			Fix:not clear the keyframe selection when select a keyframe without Shift or Ctrol key.
			Save the floating view status on setting file.
			Fix:save motion as top timeline when open the motionclip.
			Fix:not save the morphs in motionclip.
			Fix some bugs.
20 Jul 2014	V1.2.5.13
			Implemanted floating view panel.(screen tab)
			Can set view panel size.(screen tab)
			Morphs can be outputed by integrated VMD motion.
			EffectDebug tab is not shown when DockLayout.xml file status.
			Fix sume bugs.
12 Jul 2014	V1.2.5.12
			Fix:SpinEditor input bug on timeline.
			Fix:Incorrect integrated VMD file is exported when motionclip is included.
			Fix:Motion layer is not shown when load MVD file.
			Fix:Previous object values is adapted when CONTROLOBJECT (self) parameter is set and the object doesn't have the parameter 
			Fix:EffectDebugTab is not shown when EffectDebug is enabled.
			Fix:Fix:MMDPass="edge" is not executed with OFFSCREENTARGET
			Fix:Render order is incorrect when the specific situration.
			Fix some bugs.
30 Jun 2014	V1.2.5.11
			Fix not valid Z-Gravity spin control.
			Change the rotation inherit order.
			Fix some bugs.
21 Jun 2014	V1.2.5.10
			Fix the bug about loading MotionClip.
			Fix the loading Textur3D/TextureCube without ResourceType.
			Fix some bugs.
03 May 2014	V1.2.5.9
			Revise LSPSM.
			Fix some bugs.
08 Apr 2014	V1.2.5.8
			Remove Windows XP on MMM require environment.
			Can default background color from settings.
			Fix some bugs.
05 Apr 2014	V1.2.5.7
			Fix Softbofy Anchor position is invalid sometimes.
			Fix SoftShadow is not refrected on Accessory.
			Fix a fatal error is occurs when load or unload physics.
			Fix related bone is not valid on Effect.
			Fix some bugs.
30 Mar 2014	V1.2.5.6
			Fix right/left arrow key about model is enable with spin or text edit control.
			Fix not enabled audio property dialog ok/cancel button.
			Fix camera alpha slider control.
			Fix an error occurs on effect assign dialog width specific situation.
			Fix an error occurs on export motion dialog with specific situation.
			Add open readme button on Model Info Dialog when "<readme>" tag in Model englis comment.
			Fix some bugs.
24 Mar 2014	V1.2.5.5
			Fix physics on/off on vmd file.
23 Mar 2014	V1.2.5.4
			Supports the new vmd file format on MikuMikuMoving v9 later.
			Can on/off physics each bones.(can not interpolate)
			Fix an error occurs rarely when select camera mode
			Fix invalid morph values are passed with plugin GetFrame.
			Fix some bugs.
22 Mar 2014	V1.2.5.3
			Fix an error occurs when external bone order changed.
			Add some items on command bar.(can add/remove with drag&drop in customize）
			Effect properties look is changed.
			Add spin edit with effect slider property.
			Can change any background color.
			Can remove project place by right click.
			Fix some bugs.
22 Mar 2014	V1.2.5.2
			Fix an error occurs when external bone is set.
			Fix some bugs.
21 Mar 2014	V1.2.5.1
			Update theme
			Fix an error occurs when form minimized.
			Fix the Tone Curve display is strange.
			Fix an error occurs when loading project file with Motion Clip
			Fix some bugs.
21 Mar 2014	V1.2.5.0
			Revise interfaces
			Fix some bugs.
22 Feb 2014	V1.2.3.11
			Revise Self-Shadow.
			Fix:Last frame is not exported when integrate motion layer.
			Fix:An error occurs when audio file is loaded and move frame.
			Fix:Can not open motion clips.
			Fix some bugs.
22 Feb 2014	V1.2.3.10
			Can export VMD file integrated motion layer/clip with keyframe every frame.
			Fix some bugs.
16 Feb 2014	V1.2.3.9
			Fix the bug about rotating bone using bone dragging.
			Fix camera radius is not changed by the mouse wheel on Model Mode when camera perspective is off.
09 Feb 2014	V1.2.3.8
			Slightly modified about self-shadowing.
			Fix some bugs.
01 Feb 2014	V1.2.3.7
			Fix:effect TEXTUREVALUE doesn't updated.
			Fix:effect Loop process bug.
			Fix some bugs.
26 Jan 2014	V1.2.3.6
			Fix:Processing is heavy when Camera Mode.
			Fix:Camera position is strange when using camera move control on right-top.
			Fix:Bone operations are strange when vertical multi-screen.
			Fix some bugs.
28 Sep 2013	V1.2.3.5
			Fix the scroll position is changed when the morph selected on timeline.
			Some bugs are fixed about Effect Offscreen.
			Fix some bugs.
24 Sep 2013	V1.2.3.4
			Fix some bugs about MotionMixer.
23 Sep 2013	V1.2.3.3
			Can change start local time with audio.
			Fix the bug an erro occurs when camera, reverse, other bone paste.
			Fix some bugs.
23 Sep 2013	V1.2.3.2
			Motion Mixer is implemented.
			Revise the morph interface on Property Panel.
			Can scaling Timeline.
			Fix some bugs.
01 Sep 2013	V1.2.2.5
			With Oculus Rift, add "Follow camera when playing". Press "P" play, then the eye follow the camera motion.
			With Oculus Rift, add "Record camera when playing". Press "P" play, then record the Oculus Rift eye into keyframes.
			Fix some bugs.
25 Aug 2013	V1.2.2.4
			Add selected bones only option with Physics Recording. Record only selected bones on Active model.
			Add select all keyframes on selected bones button on bottom of timeline panel and right click contex menu.
			Fix some bugs.
24 Aug 2013	V1.2.2.3
			Add shortcut-key Regist Bookmark Ctrl+M.
			Fix some bugs.
21 Aug 2013	V1.2.2.2
			Add Key Config on settings-editor.
			Can set any Screen FPS between 1 and 60 fps.
			Can load mp4 etc. Of course, codecs is needed.
			Add screen size initialize button on AVI render dialog.
			Revise interpolate about camera move.
			Fix some bugs.
17 Aug 2013	V1.2.2.1
			Revise Oculus Rift
			Add Effect cache function. User can set the cache size on settings.
			Fix the bug doesn't enable DynamicFov when the ground shadow is enabled.
			Fix the bug an error occurs when load mvd file with Related Bone.
			Fix some bugs.
04 Aug 2013	V1.2.2.0
			Support Oculus Rift
			 Usage:
				1. Load some model,accessory,motion.
				2. Load Oculus Rift
				3. "OculusRift" tab -> "OculusRift"
				4. Equip Oculus Rift
				5. Move using mouse.
					- Left mouse button: Move forward
					- Right mouse button: Move back
					- Mouse: Look
					- Mouse wheel: Move Up/Down
					- "P" key: Play/Stop
			Fix the bug there are invalid project property when save project.
			Fix the bug a keyframe is pasted on last effect when there are multiple same name effects.
			Fix some bugs.
 - マウスの左ボタン押しっぱなしで前進、右ボタンで後進です。
			　　- マウスを動かすと、移動方向(横)を決められます。
				- マウスホイールで上下移動ができます。
				- "P"ボタンでモーション再生/停止します。
			v1.2.1.10にて、エフェクト使用時に地面影が常に表示されてしまっていたバグ修正
			全体プロパティの保存がおかしかったバグ修正
			同名のエフェクトが複数ある場合に、キーフレームのペーストが最後のエフェクトに強制的にペーストされるバグ修正
			その他細々修正
27 Jul 2013	V1.2.1.10
			Add full screen mode.
			Fix the bug an error occurs when the model having 4 adding UV.
			Fix the bug invalid vpd file is output on comma decimal marker environment.
			Fix the bug the technique with MMDPass "edge" or "shadow" is not processed on OffscreenEffect.
			Fix the bug invalid ELAPSEDTIME value when the effect having Offscreen exists.
			Fix some bugs.
14 Jul 2013	V1.2.1.9
			Can move row with up/down key beyond the folder.
			Add LSPSM self-shadow on camera mode self-shadow tab.
			Revise include function on Effect.
			Revise bone-morph + inhere-move.
			Revise subtexture implementation.
			Fix the bug an error occurs when paset camera-layer keyframe.
			Fix the bug offscreen annotation "hide","none" keyword don't work on Effect.
			Revise CONTROLOBJECT annotation implementation on Effect.
			Revise Subset annotation implementation on Effect.
			Fix some bugs.
18 Jun 2013	V1.2.1.8
			Fix the bug regist keyframes after select unregisted bones on specific situration.
			Fix the bug can not disable assosiation with Accessory.
			Fix some bugs.
15 Jun 2013	V1.2.1.7
			Fix the bug an error occured when disable character related bone.
			Fix some bugs
09 Jun 2013	V1.2.1.6
			Revise (Fix the bone rotation and position when disable its related bone)
			Open a Model and accessory file as CommandLine Argument.
08 Jun 2013	V1.2.1.5
			Camera can follow a bone set with Camera Property Panel.
			Fix the bone rotation and position when disable its related bone with Accessory.
			Fix the bug an error is occured when regist keyframe on camera layer.
			Fix some bugs.
08 Jun 2013	V1.2.1.4
			Supports VMD for MikuMikuDance v7.42
			Fix the bone rotation and position when disable its related bone.
			Fix the bug an error occurs when delete camera keyframes.
			Fix the bug Bone Reversal Paste.
			Fix some bugs.
02 Jun 2013	V1.2.1.3
			Fix the ik bone rotation when disable its ik.
			Revise Accessory selfshadow.
			Fix some bugs.
02 Jun 2013	V1.2.1.2
			Add function "AdjustPosition" on Bone tab.
			 * Paste a copied keyframe absolute position into other bone.
			 Usage
			  1. Copy a keyframe you want to copy position
			　2. Select target bone
			　3. Clidk "AdjustPosition" button
			Fix some bugs.
26 May 2013	V1.2.1.1
			Can change Locus point size on settings.
			Add function of showing camera.
			Add function of showing camera locus.
			Change bookmark shortcuts.
			Fix the bug can not select unregistered bone when show locus is on.
			Fix the bug an error is occured when show accessory information with FBX or OBJ file.
			Fix some bugs.
18 May 2013	V1.2.1.0
			Add spline move and rotate with Camera motion.
			Can load .fbx file as Accessory.
			Can load .obj file as Accessory.
			Add output scene as fbx file (provisional).
			Add some command bar.
			Add shortcats about bookmark.
			Fix some bugs.
05 May 2013	V1.2.0.0
			Add the function to show only expanded bones with view tab.
			Revise sphere texture alpha formula.
			Fix some bugs.
04 May 2013	V1.1.9.13
			Revise material morph - multiply sphere.
04 May 2013	V1.1.9.12
			Fix MipMap is not effective when using SelfShadow.
			Fix some bugs.
02 May 2013	V1.1.9.11
			Revise Dynamic Fov fomula
			Fix the bug SDEF when attaching shader into model.
			Revise SampleBase.fxm effect file.
30 Apr 2013	V1.1.9.10
			Implemented Dynamic Fov(need PS3.0) on CameraProperty.
			Fix the bug Bone handle is not shown when specific situation.
			Fix the bug Edge Size when using Material morph.
			Fix the bug SDEF skinning when model size is changed.
			Fix some bugs.
31 Mar 2013	V1.1.9.9
			Revise Physics
24 Mar 2013	V1.1.9.8
			Revise loading BVH motion file.
			Fix the bug an error occurs when adding audio track.
			Revise the Transform after Physics.
			Fix some bugs.
16 Mar 2013	V1.1.9.7
			The textures are not loaded when the device lost under certain conditions.
			Add text file listview on the model information dialog.
			Fix some bugs.
14 Mar 2013	V1.1.9.6
			Delete zip loading function
10 Mar 2013	V1.1.9.5
			Fix some bugs.
10 Mar 2013	V1.1.9.4
			Can load ZIP model and accessory file.
			Fix the bug "paste this bone" from right mouse click.
			Revise the inhere move bone.
			Fix some bugs.
03 Mar 2013	V1.1.9.3
			Select the center bone when rotating bone with Ctrl+Shift keys.
			Fix the effect compiler error dialog bug.
			Fix some bugs.
02 Mar 2013	V1.1.9.2
			Add Debug Effect mode
			Improve the error dialog when a effect is loading.
			Fix a polygon isn't shown sometimes when using spline motion.
			Fix the size isn't changed when output image.
			Fix some bugs.
21 Feb 2013	V1.1.9.1
			Fix the bug an error occurs when the locus is shown.
			Fix the bug strange locus is shown sometimes.
			Fix the bug the filter fade value is not saved.
			Fix some bugs
20 Feb 2013	V1.1.9.0
			Add Locus(Motion path) function.
			 1. Right click on timeline bone title and select lucus bone
			 2. Enable "Show Locus" on View tab.
			 3. Motion path is shown on screen.
			Add "spline" flag into bone keyframe.the keyframe rote/move is interpolated.
			Fix some bugs
10 Feb 2013	V1.1.8.10
			Add Related parent ordering (Screen Tab)
			Can copy file path on Model or Accessory information dialog
			Add enable screen button on Screen Tab
			Fix some bugs
04 Feb 2013	V1.1.8.9
			Add Filter property on camera timeline.
			　* Tone curve, gray scale, sepia, fade, HSV
			　* Can regist as keyframe
			　* Can select interpolation between keyframes
			Fix the bug saved file is incorrect when set the image or movie on Screen Property.
			Fix some bugs
01 Feb 2013	V1.1.8.8
			Add renaming model/accessory/effect/camera
			　* Model: model button right click
			　* Accessory/Effect: model button right click or timeline title right click or double click
			　* Camera: timeline title right click or double click
			Add Copy all interpolate 
			Fix some bugs.
27 Jan 2013	V1.1.8.7
			Separate camera property (Enable, Effect, Alpha, Perspective)
			Revise softbody.
			Fix the bug some effect don't work.
			Fix some bugs.
23 Jan 2013	V1.1.8.6
			Add Camera alpha and effect enable/disable property
			Attach a camera into object screen
			Change the interpol value on timeline, then the keyframe is selected
			Move row by Up or Down key
			Select Project property by End key when Camera Mode
			Move zero frame by Home key
			Fix some bugs
20 Jan 2013	V1.1.8.5
			Multi Camera (provisional)
			Revise SDEF algorithm (complete)
			Fix some bugs
19 Jan 2013	V1.1.8.4
			Fix the bug Accessory path can not be saved correctly.
			Revise Local Inhere function.
18 Jan 2013	V1.1.8.3
			Sync the interpolate curve item selected between TimeLine and left bottom Panel.
			Change the color on selected bone folder.
			Revise SDEF algorithm
			Fix the some bug about effect
			Fix some bugs
12 Jan 2013	V1.1.8.2
			Add insert/remove column target selector
			Revise Local Inhere function
12 Jan 2013	V1.1.8.1
			Add Local Inhere function on PMX model
			Revise SDEF algorithm
			Fix some bugs
06 Jan 2013	V1.1.8.0
			Add editable interpolate curve on Camera TimeLine
			Revise SDEF algorithm
			Fix some bugs
05 Jan 2013	V1.1.7.11
			Fix some bugs about timeline interpolate curve.
05 Jan 2013	V1.1.7.10
			Revise SDEF algorithm(provisional).
			Add editable interpolate cureve on TimeLine(lower right button of TimeLine).
			 * Only bone motion
04 Nov 2012	V1.1.7.9
			Effect do the material with 'Screen.bmp' image.
			Fix:An error occurs when using effect with APNG image.
			Fix:Specular doesn't effect in Accessory.
			Fix:Caption position and size are strange when outputting image.
			Fix some bugs
08 Oct 2012	V1.1.7.8
			There might be something good if you look Shortcut keys list.
			Fix some bugs
04 Oct 2012	V1.1.7.6
			Change the behavior in Inhere Rotation for PMX
			Aspect rate is depended only output size on rendering dialog.
			Adjust about Physics and Recording physics functions.
			Fix some bugs
01 Oct 2012	V1.1.7.5
			Supports import BVH motion file.
			Fix some bugs
28 Sep 2012	V1.1.7.4
			Supports rope for soft body physics
			Fix:An effect related a bone doesn't move when playing.
			Fix some bugs
23 Sep 2012	V1.1.7.3
			Fix:Strange initialize soft body
			Fix some bugs
23 Sep 2012	V1.1.7.2
			The vertices had same position in the same material are as the one vertex for SoftBody
			Fix:SDEF vertex for SoftBody
			Fix some bugs
23 Sep 2012	V1.1.7.1
			Fix:MMM is freezed when Physics:OFF->SoftBody:OFF->SoftBody:ON->Physics:ON
22 Sep 2012	V1.1.7.0
			Supports soft body physics for PMX2.1
			Fix some bugs
21 Sep 2012	V1.1.6.7
			Fix:An accessory related a bone doesn't move when playing.
			Fix some bugs
17 Sep 2012	V1.1.6.6
			Draw reverse side line or point darawing.
			Fix some bugs
16 Sep 2012	V1.1.6.5
			Supports point and line drawing for PMX2.1
			Fix some bugs.
16 Sep 2012	V1.1.6.4
			Rebuild Undo/Redo
			Fix the bug an error occurs when auto backup.
			Fix some bugs.
14 Sep 2012 V1.1.6.3
			Add Frame Timeline.You can move the entire timeline. And you can show/hide using the button to the right of volume.
			Fix the bug model scaling doesn't effect on v1.1.6.2
			Fix the bug strange move/rotate in an accessory.
			Fix the bug a immidiate created caption's position is strange when output image etc.
			Fix some bugs.
11 Sep 2012 V1.1.6.2
			The bones have no parent are affected when setting the related bone on the root.
			Fix some bugs.
11 Sep 2012	V1.1.6.1
			Fix some bugs.
10 Sep 2012	V1.1.6.0
			The model that have moving root bone and external bone can relate the other model bone.
			 * The process is executed with the rendering order.
			The model or accessory related other model is scaled.
			Toggle model/accessory/camera with Tab key.
			The bug that motion layers don't shown after editing display frames is fixed.
			The bug that registing camera layer motion is strange is fixed.
			Fix some bugs.
08 Sep 2012 V1.1.5.1
			Fix some bugs.
07 Sep 2012 V1.1.5.0
			Rotate the parent bone like cancel bone when rotate the child bone with Alt key.
			Rotate the child bone <-> parent bone when rotate with Ctrl+Shift keys.(Need center bone)
			A littele arrange manipulate the bone
			Can select 2 theme in settings.
			Can edit the display frame and save it in project file.
			Can save the frame position in project file.
			Fix some bugs.
30 Aug 2012	V1.1.4.5
			Fix the bug an error occures when physics is off.
29 Aug 2012	V1.1.4.4
			Fix the bug an error occures when loading the no rigid body model.
29 Aug 2012	V1.1.4.3
			Fix the bug an error occures when model scale is changed.
			Disable physics when the rigid bodies are too small.
			Physics can work when the model scale is changing.
			Fix some bugs
27 Aug 2012 V1.1.4.0
			Add model scale property
			Rigids is moved with zero velocity when model physics property OFF->ON
			Remove the rigids when model physics property is OFF or model is invisible
			Fix some bugs
25 Aug 2012 V1.1.3.0
			Save the background color in project file.
			Add plugin APIs
			　Scene.Volume property
			　Scene.AudioTracks
			　SceneFrameData.Noise
			　ScreenImage_2D.VisibleWhenPlaying flug
			Change the behavior Bone and MotionLayer CurrentLocalMotion
			Fix the bug CurrentLocalMotion doesn't work
			Fix the bug EDGECOLOR doesn't work in effect
			Fix some bugs
23 Aug 2012	V1.1.2.6
			Fix the critical bug when multi model loaded.
			Revise "#include" support in Effect.
22 Aug 2012	V1.1.2.5
			Support "shared" parameter in Effect.
			Support "#include" in Effect.
			Bug fix moving accessory related other bone
			Fix some bugs
18 Aug 2012	V1.1.2.3
			Fix the bug can't run on PixelShader2.0 environment
18 Aug 2012 V1.1.2.2
			Fix some bugs
17 Aug 2012 V1.1.2.0
			.NET Framework 4.0 is required from this version
			Tuning performance
			Add MipMap and Anisotropic texture filtering function (settings dialog)
			Add noise function on gravity property
			Fix the bug that a effect boolean UI is not shown.
			Fix some bugs
08 Aug 2012 V1.1.1.1
			Fix the bug effect can't load a texture on v1.1.1.0
			Fix the bug motion layer name on plugin
			Fix a error is occured when effect dynamic loading
			Fix some bugs
05 Aug 2012 V1.1.1.0
			"Record Physics" function is changed. Start frame is current frame.
			Add "Record Physics between bookmarks"
			Plugin APIs is added and changed.
			Fix select range on morphs bug
			Fix some bugs
04 Aug 2012	V1.1.0.4
			Auto scrolling for range selection and move keyframe on timeline.
			Adjusting "Sound when move frame" function
			Fix the bug on Effect Assign dialog.
			Fix:Stop the audio when putting many audio file and play.
			Fix some bugs
03 Aug 2012	V1.1.0.3
			Change the finely of manupilation when down Ctrl key.
			Fix the caption position shift when rendering AVI.
			Fix the position of times font on caption.
			Fix:A error occure when removing the model texture is set but the texture file doesn't exist.
			Fix:MMM can't start when main screen is floating and exit.
			Problem for relating model on a accessory when using a plugin is fixed.
			Fix some bugs
09 Jun 2012	V1.0
01 Jan 2012	V0.4	Beta version
29 Aug 2011	V0.2	Alpha version
14 Aug 2011	V0.1	Preview version


Licenses
========================================================
MikuMikuMoving uses the following softwares.

Ms-PL: DotNetZip Library
MIT License:SlimDX, Bulletsharp
BSD Style License:ZLIB.NET
LGPL License:DirectShowLib


License
========================================================
DotNetZip Library

Sponsored by: Xceed
http://dotnetzip.codeplex.com/


License
========================================================
SlimDX

Copyright (c) 2007-2009 SlimDX Group

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

========================================================
Bulletsharp (http://code.google.com/p/bulletsharp/)

Copyright (c) andres.traks

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.


========================================================
ZLIB.NET

Copyright (c) 2006-2007, ComponentAce
http://www.componentace.com
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer. 
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution. 
Neither the name of ComponentAce nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission. 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


DirectShowLibNET V2.0
http://directshownet.sourceforge.net/
==================================================================================

		  GNU LESSER GENERAL PUBLIC LICENSE
		       Version 2.1, February 1999

 Copyright (C) 1991, 1999 Free Software Foundation, Inc.
     51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

[This is the first released version of the Lesser GPL.  It also counts
 as the successor of the GNU Library Public License, version 2, hence
 the version number 2.1.]

			    Preamble

  The licenses for most software are designed to take away your
freedom to share and change it.  By contrast, the GNU General Public
Licenses are intended to guarantee your freedom to share and change
free software--to make sure the software is free for all its users.

  This license, the Lesser General Public License, applies to some
specially designated software packages--typically libraries--of the
Free Software Foundation and other authors who decide to use it.  You
can use it too, but we suggest you first think carefully about whether
this license or the ordinary General Public License is the better
strategy to use in any particular case, based on the explanations below.

  When we speak of free software, we are referring to freedom of use,
not price.  Our General Public Licenses are designed to make sure that
you have the freedom to distribute copies of free software (and charge
for this service if you wish); that you receive source code or can get
it if you want it; that you can change the software and use pieces of
it in new free programs; and that you are informed that you can do
these things.

  To protect your rights, we need to make restrictions that forbid
distributors to deny you these rights or to ask you to surrender these
rights.  These restrictions translate to certain responsibilities for
you if you distribute copies of the library or if you modify it.

  For example, if you distribute copies of the library, whether gratis
or for a fee, you must give the recipients all the rights that we gave
you.  You must make sure that they, too, receive or can get the source
code.  If you link other code with the library, you must provide
complete object files to the recipients, so that they can relink them
with the library after making changes to the library and recompiling
it.  And you must show them these terms so they know their rights.

  We protect your rights with a two-step method: (1) we copyright the
library, and (2) we offer you this license, which gives you legal
permission to copy, distribute and/or modify the library.

  To protect each distributor, we want to make it very clear that
there is no warranty for the free library.  Also, if the library is
modified by someone else and passed on, the recipients should know
that what they have is not the original version, so that the original
author's reputation will not be affected by problems that might be
introduced by others.



  Finally, software patents pose a constant threat to the existence of
any free program.  We wish to make sure that a company cannot
effectively restrict the users of a free program by obtaining a
restrictive license from a patent holder.  Therefore, we insist that
any patent license obtained for a version of the library must be
consistent with the full freedom of use specified in this license.

  Most GNU software, including some libraries, is covered by the
ordinary GNU General Public License.  This license, the GNU Lesser
General Public License, applies to certain designated libraries, and
is quite different from the ordinary General Public License.  We use
this license for certain libraries in order to permit linking those
libraries into non-free programs.

  When a program is linked with a library, whether statically or using
a shared library, the combination of the two is legally speaking a
combined work, a derivative of the original library.  The ordinary
General Public License therefore permits such linking only if the
entire combination fits its criteria of freedom.  The Lesser General
Public License permits more lax criteria for linking other code with
the library.

  We call this license the "Lesser" General Public License because it
does Less to protect the user's freedom than the ordinary General
Public License.  It also provides other free software developers Less
of an advantage over competing non-free programs.  These disadvantages
are the reason we use the ordinary General Public License for many
libraries.  However, the Lesser license provides advantages in certain
special circumstances.

  For example, on rare occasions, there may be a special need to
encourage the widest possible use of a certain library, so that it becomes
a de-facto standard.  To achieve this, non-free programs must be
allowed to use the library.  A more frequent case is that a free
library does the same job as widely used non-free libraries.  In this
case, there is little to gain by limiting the free library to free
software only, so we use the Lesser General Public License.

  In other cases, permission to use a particular library in non-free
programs enables a greater number of people to use a large body of
free software.  For example, permission to use the GNU C Library in
non-free programs enables many more people to use the whole GNU
operating system, as well as its variant, the GNU/Linux operating
system.

  Although the Lesser General Public License is Less protective of the
users' freedom, it does ensure that the user of a program that is
linked with the Library has the freedom and the wherewithal to run
that program using a modified version of the Library.

  The precise terms and conditions for copying, distribution and
modification follow.  Pay close attention to the difference between a
"work based on the library" and a "work that uses the library".  The
former contains code derived from the library, whereas the latter must
be combined with the library in order to run.



		  GNU LESSER GENERAL PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. This License Agreement applies to any software library or other
program which contains a notice placed by the copyright holder or
other authorized party saying it may be distributed under the terms of
this Lesser General Public License (also called "this License").
Each licensee is addressed as "you".

  A "library" means a collection of software functions and/or data
prepared so as to be conveniently linked with application programs
(which use some of those functions and data) to form executables.

  The "Library", below, refers to any such software library or work
which has been distributed under these terms.  A "work based on the
Library" means either the Library or any derivative work under
copyright law: that is to say, a work containing the Library or a
portion of it, either verbatim or with modifications and/or translated
straightforwardly into another language.  (Hereinafter, translation is
included without limitation in the term "modification".)

  "Source code" for a work means the preferred form of the work for
making modifications to it.  For a library, complete source code means
all the source code for all modules it contains, plus any associated
interface definition files, plus the scripts used to control compilation
and installation of the library.

  Activities other than copying, distribution and modification are not
covered by this License; they are outside its scope.  The act of
running a program using the Library is not restricted, and output from
such a program is covered only if its contents constitute a work based
on the Library (independent of the use of the Library in a tool for
writing it).  Whether that is true depends on what the Library does
and what the program that uses the Library does.
  
  1. You may copy and distribute verbatim copies of the Library's
complete source code as you receive it, in any medium, provided that
you conspicuously and appropriately publish on each copy an
appropriate copyright notice and disclaimer of warranty; keep intact
all the notices that refer to this License and to the absence of any
warranty; and distribute a copy of this License along with the
Library.

  You may charge a fee for the physical act of transferring a copy,
and you may at your option offer warranty protection in exchange for a
fee.



  2. You may modify your copy or copies of the Library or any portion
of it, thus forming a work based on the Library, and copy and
distribute such modifications or work under the terms of Section 1
above, provided that you also meet all of these conditions:

    a) The modified work must itself be a software library.

    b) You must cause the files modified to carry prominent notices
    stating that you changed the files and the date of any change.

    c) You must cause the whole of the work to be licensed at no
    charge to all third parties under the terms of this License.

    d) If a facility in the modified Library refers to a function or a
    table of data to be supplied by an application program that uses
    the facility, other than as an argument passed when the facility
    is invoked, then you must make a good faith effort to ensure that,
    in the event an application does not supply such function or
    table, the facility still operates, and performs whatever part of
    its purpose remains meaningful.

    (For example, a function in a library to compute square roots has
    a purpose that is entirely well-defined independent of the
    application.  Therefore, Subsection 2d requires that any
    application-supplied function or table used by this function must
    be optional: if the application does not supply it, the square
    root function must still compute square roots.)

These requirements apply to the modified work as a whole.  If
identifiable sections of that work are not derived from the Library,
and can be reasonably considered independent and separate works in
themselves, then this License, and its terms, do not apply to those
sections when you distribute them as separate works.  But when you
distribute the same sections as part of a whole which is a work based
on the Library, the distribution of the whole must be on the terms of
this License, whose permissions for other licensees extend to the
entire whole, and thus to each and every part regardless of who wrote
it.

Thus, it is not the intent of this section to claim rights or contest
your rights to work written entirely by you; rather, the intent is to
exercise the right to control the distribution of derivative or
collective works based on the Library.

In addition, mere aggregation of another work not based on the Library
with the Library (or with a work based on the Library) on a volume of
a storage or distribution medium does not bring the other work under
the scope of this License.

  3. You may opt to apply the terms of the ordinary GNU General Public
License instead of this License to a given copy of the Library.  To do
this, you must alter all the notices that refer to this License, so
that they refer to the ordinary GNU General Public License, version 2,
instead of to this License.  (If a newer version than version 2 of the
ordinary GNU General Public License has appeared, then you can specify
that version instead if you wish.)  Do not make any other change in
these notices.



  Once this change is made in a given copy, it is irreversible for
that copy, so the ordinary GNU General Public License applies to all
subsequent copies and derivative works made from that copy.

  This option is useful when you wish to copy part of the code of
the Library into a program that is not a library.

  4. You may copy and distribute the Library (or a portion or
derivative of it, under Section 2) in object code or executable form
under the terms of Sections 1 and 2 above provided that you accompany
it with the complete corresponding machine-readable source code, which
must be distributed under the terms of Sections 1 and 2 above on a
medium customarily used for software interchange.

  If distribution of object code is made by offering access to copy
from a designated place, then offering equivalent access to copy the
source code from the same place satisfies the requirement to
distribute the source code, even though third parties are not
compelled to copy the source along with the object code.

  5. A program that contains no derivative of any portion of the
Library, but is designed to work with the Library by being compiled or
linked with it, is called a "work that uses the Library".  Such a
work, in isolation, is not a derivative work of the Library, and
therefore falls outside the scope of this License.

  However, linking a "work that uses the Library" with the Library
creates an executable that is a derivative of the Library (because it
contains portions of the Library), rather than a "work that uses the
library".  The executable is therefore covered by this License.
Section 6 states terms for distribution of such executables.

  When a "work that uses the Library" uses material from a header file
that is part of the Library, the object code for the work may be a
derivative work of the Library even though the source code is not.
Whether this is true is especially significant if the work can be
linked without the Library, or if the work is itself a library.  The
threshold for this to be true is not precisely defined by law.

  If such an object file uses only numerical parameters, data
structure layouts and accessors, and small macros and small inline
functions (ten lines or less in length), then the use of the object
file is unrestricted, regardless of whether it is legally a derivative
work.  (Executables containing this object code plus portions of the
Library will still fall under Section 6.)

  Otherwise, if the work is a derivative of the Library, you may
distribute the object code for the work under the terms of Section 6.
Any executables containing that work also fall under Section 6,
whether or not they are linked directly with the Library itself.



  6. As an exception to the Sections above, you may also combine or
link a "work that uses the Library" with the Library to produce a
work containing portions of the Library, and distribute that work
under terms of your choice, provided that the terms permit
modification of the work for the customer's own use and reverse
engineering for debugging such modifications.

  You must give prominent notice with each copy of the work that the
Library is used in it and that the Library and its use are covered by
this License.  You must supply a copy of this License.  If the work
during execution displays copyright notices, you must include the
copyright notice for the Library among them, as well as a reference
directing the user to the copy of this License.  Also, you must do one
of these things:

    a) Accompany the work with the complete corresponding
    machine-readable source code for the Library including whatever
    changes were used in the work (which must be distributed under
    Sections 1 and 2 above); and, if the work is an executable linked
    with the Library, with the complete machine-readable "work that
    uses the Library", as object code and/or source code, so that the
    user can modify the Library and then relink to produce a modified
    executable containing the modified Library.  (It is understood
    that the user who changes the contents of definitions files in the
    Library will not necessarily be able to recompile the application
    to use the modified definitions.)

    b) Use a suitable shared library mechanism for linking with the
    Library.  A suitable mechanism is one that (1) uses at run time a
    copy of the library already present on the user's computer system,
    rather than copying library functions into the executable, and (2)
    will operate properly with a modified version of the library, if
    the user installs one, as long as the modified version is
    interface-compatible with the version that the work was made with.

    c) Accompany the work with a written offer, valid for at
    least three years, to give the same user the materials
    specified in Subsection 6a, above, for a charge no more
    than the cost of performing this distribution.

    d) If distribution of the work is made by offering access to copy
    from a designated place, offer equivalent access to copy the above
    specified materials from the same place.

    e) Verify that the user has already received a copy of these
    materials or that you have already sent this user a copy.

  For an executable, the required form of the "work that uses the
Library" must include any data and utility programs needed for
reproducing the executable from it.  However, as a special exception,
the materials to be distributed need not include anything that is
normally distributed (in either source or binary form) with the major
components (compiler, kernel, and so on) of the operating system on
which the executable runs, unless that component itself accompanies
the executable.

  It may happen that this requirement contradicts the license
restrictions of other proprietary libraries that do not normally
accompany the operating system.  Such a contradiction means you cannot
use both them and the Library together in an executable that you
distribute.



  7. You may place library facilities that are a work based on the
Library side-by-side in a single library together with other library
facilities not covered by this License, and distribute such a combined
library, provided that the separate distribution of the work based on
the Library and of the other library facilities is otherwise
permitted, and provided that you do these two things:

    a) Accompany the combined library with a copy of the same work
    based on the Library, uncombined with any other library
    facilities.  This must be distributed under the terms of the
    Sections above.

    b) Give prominent notice with the combined library of the fact
    that part of it is a work based on the Library, and explaining
    where to find the accompanying uncombined form of the same work.

  8. You may not copy, modify, sublicense, link with, or distribute
the Library except as expressly provided under this License.  Any
attempt otherwise to copy, modify, sublicense, link with, or
distribute the Library is void, and will automatically terminate your
rights under this License.  However, parties who have received copies,
or rights, from you under this License will not have their licenses
terminated so long as such parties remain in full compliance.

  9. You are not required to accept this License, since you have not
signed it.  However, nothing else grants you permission to modify or
distribute the Library or its derivative works.  These actions are
prohibited by law if you do not accept this License.  Therefore, by
modifying or distributing the Library (or any work based on the
Library), you indicate your acceptance of this License to do so, and
all its terms and conditions for copying, distributing or modifying
the Library or works based on it.

  10. Each time you redistribute the Library (or any work based on the
Library), the recipient automatically receives a license from the
original licensor to copy, distribute, link with or modify the Library
subject to these terms and conditions.  You may not impose any further
restrictions on the recipients' exercise of the rights granted herein.
You are not responsible for enforcing compliance by third parties with
this License.



  11. If, as a consequence of a court judgment or allegation of patent
infringement or for any other reason (not limited to patent issues),
conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot
distribute so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you
may not distribute the Library at all.  For example, if a patent
license would not permit royalty-free redistribution of the Library by
all those who receive copies directly or indirectly through you, then
the only way you could satisfy both it and this License would be to
refrain entirely from distribution of the Library.

If any portion of this section is held invalid or unenforceable under any
particular circumstance, the balance of the section is intended to apply,
and the section as a whole is intended to apply in other circumstances.

It is not the purpose of this section to induce you to infringe any
patents or other property right claims or to contest validity of any
such claims; this section has the sole purpose of protecting the
integrity of the free software distribution system which is
implemented by public license practices.  Many people have made
generous contributions to the wide range of software distributed
through that system in reliance on consistent application of that
system; it is up to the author/donor to decide if he or she is willing
to distribute software through any other system and a licensee cannot
impose that choice.

This section is intended to make thoroughly clear what is believed to
be a consequence of the rest of this License.

  12. If the distribution and/or use of the Library is restricted in
certain countries either by patents or by copyrighted interfaces, the
original copyright holder who places the Library under this License may add
an explicit geographical distribution limitation excluding those countries,
so that distribution is permitted only in or among countries not thus
excluded.  In such case, this License incorporates the limitation as if
written in the body of this License.

  13. The Free Software Foundation may publish revised and/or new
versions of the Lesser General Public License from time to time.
Such new versions will be similar in spirit to the present version,
but may differ in detail to address new problems or concerns.

Each version is given a distinguishing version number.  If the Library
specifies a version number of this License which applies to it and
"any later version", you have the option of following the terms and
conditions either of that version or of any later version published by
the Free Software Foundation.  If the Library does not specify a
license version number, you may choose any version ever published by
the Free Software Foundation.



  14. If you wish to incorporate parts of the Library into other free
programs whose distribution conditions are incompatible with these,
write to the author to ask for permission.  For software which is
copyrighted by the Free Software Foundation, write to the Free
Software Foundation; we sometimes make exceptions for this.  Our
decision will be guided by the two goals of preserving the free status
of all derivatives of our free software and of promoting the sharing
and reuse of software generally.

			    NO WARRANTY

  15. BECAUSE THE LIBRARY IS LICENSED FREE OF CHARGE, THERE IS NO
WARRANTY FOR THE LIBRARY, TO THE EXTENT PERMITTED BY APPLICABLE LAW.
EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR
OTHER PARTIES PROVIDE THE LIBRARY "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE
LIBRARY IS WITH YOU.  SHOULD THE LIBRARY PROVE DEFECTIVE, YOU ASSUME
THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN
WRITING WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY
AND/OR REDISTRIBUTE THE LIBRARY AS PERMITTED ABOVE, BE LIABLE TO YOU
FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR
CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE
LIBRARY (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA BEING
RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A
FAILURE OF THE LIBRARY TO OPERATE WITH ANY OTHER SOFTWARE), EVEN IF
SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
DAMAGES.

		     END OF TERMS AND CONDITIONS


