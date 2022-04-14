<div id="top"></div>
<!-- ABOUT THE PROJECT -->

## Work-Split-Tracker

Work-Split-Tracker is a tray application that helps you stay focused, motivated and overall boosts your productivity. 

Complex tasks can easily become overwhelming without proper time management and prioritization. This application is trying to solve this problem by helping you to avoid losing focus and getting demotivated. Especially when working on a tight schedule it is import to take periodic brakes to stay productive. Therefore, the Work-Split-Tracker allows you to define the time you want to work per session as well as the length of the break you want to take afterwards. This drastically helps you to stay focused. But even managing your time this way does not ensure that you will stay productive. In order to not only stay focused but also motivated it is important to split up and prioritize your work. Therfore, the Work-Split-Tracker lets you create tasks and assign those to a work session. Additionally, tasks can be assigned a priority as well as an estimated workload (i.e. how many work session are needed to complete that task). This helps you track your progression and gets your project running faster. Therefore, even complex tasks can be tackled easily.


<!-- GETTING STARTED -->
## Prerequisites

In order to run this application from source you need to satisfy the following prerequisites:

- Python 3.6

## Getting Started

For Windows and Ubuntu the installer can be used which is automatically build for every realese (https://github.com/rMieep/work-split-tracker/releases).

People who want to run the application from source or do not use Windows/Ubuntu can do that by follwing the next steps:

1. Clone the repo
   ```sh
   git clone https://github.com/rMieep/work-split-tracker.git
   ```
   
2. Create and activate a virtual enviroment (Optional)
   
   On Linux or Mac:
   ```sh
   python3 -m venv path/to/venv
   source path/to/venv/bin/activate
   ```
   
   On Windows:
   ```sh
   python -m venv path\to\venv
   path\to\venv\Scripts\activate.bat
   ```
3. Upgrade PIP
   
   On Linux or Mac
   ```sh
   pip install --upgrade pip
   ```
   
   On Windows:
   ```sh
   python -m pip install --upgrade pip
   ```
   
4. Install pip packages
   ```sh
   pip install -r requirements.txt
   ```

5. Run the program
   ```sh
   fbs run
   ```

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- Usage -->
## Usage
Once the program runs the user can access it throught the system tray. 

![Tray](https://github.com/rMieep/work-split-tracker-private/blob/master/assets/Tray%20_Edited.png)

The context menu can be opended by right clicking the icon. From the context menu additional windows can be opened.

![Tray Icon Context Menu](https://github.com/rMieep/work-split-tracker-private/blob/master/assets/Tray_Context_Menu.png)

If the user wants to assign a task to his work session he can open the TimerWindow by clicking on the timer (first menu item).

![Timer Window Work](https://github.com/rMieep/work-split-tracker-private/blob/master/assets/Timer_Window_Work_Edited.png)
![Timer Window Break](https://github.com/rMieep/work-split-tracker-private/blob/master/assets/Timer_Window_Break_Edited.png)

If the user wants to create new tasks or manage existing ones he can click on the Backlog menu option (fourth menu item)

![Backlog Window](https://github.com/rMieep/work-split-tracker-private/blob/master/assets/Backlog_window_Edited.png)

Finnaly, the user can configure the program behavior by clicking the Settings menu option (seventh menu item)

![Settings Window](https://github.com/rMieep/work-split-tracker-private/blob/master/assets/Settings_Window.png)


<p align="right">(<a href="#top">back to top</a>)</p>

<!-- Acknowledgment -->
## Acknowledgment

- https://github.com/trappitsch/fbs-release-github-actions for a good example on how to automatically create installers using fbs and github actions.

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>
