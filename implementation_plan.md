**Implementation Plan: Missing UI/UX Features**  
This plan outlines the steps to resolve the three missing features you reported: seeing other users' posts (Global Feed), discovering people to follow (User Search), and allowing multi-line text in the message input.  
**User Review Required**  
*[!IMPORTANT]*  
- *I will install * *react-textarea-autosize* * in the frontend to make the message input box expand seamlessly as you type multiple lines.*  
- *I will create a new * ***Explore*** * page (accessed via a magnifying glass icon on the left sidebar). This page will contain a search bar to find users and a "Global Feed" showing all posts across the platform so you can discover content.*  
- *Please review this approach and let me know if it aligns with your vision!*  
**Proposed Changes**  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAM0lEQVR4nO3OUQmAABBAsaeI2MKqV8RyJrGCfyJsCbbMzFldAQDwF/dWrdXx9QQAgNf2B/NkAzRb7P0YAAAAAElFTkSuQmCC)  
**1. Backend: Global Feed Endpoint**  
***[MODIFY] *** *app/modules/posts/service.py*  
- Add a new global_timeline function that queries all posts without filtering by the viewer's followees.  
***[MODIFY] *** *app/modules/posts/router.py*  
- Add GET /global endpoint returning the results of global_timeline.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNhwgJuUPYDMpnRgQU2QtIq6DIze3UGAMBf3Gu1VcfXEwAAXrseaHEEM+cJoFcAAAAASUVORK5CYII=)  
**2. Frontend: API Integration**  
***[MODIFY] *** *frontend/src/api/posts.ts*  
- Add globalFeed API call.  
***[MODIFY] *** *frontend/src/api/users.ts*  
- Add searchUsers(query: string) API call.  
***[MODIFY] *** *frontend/src/features/feed/useFeed.ts*  
- Add useGlobalFeed infinite query hook.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQmAABRAsSdYxZ4/mJjEsxE8W8GbCFuCLTOzVXsAAPzFuVZ3dXw9AQDgtesBxPEF3bv7x0IAAAAASUVORK5CYII=)  
**3. Frontend: Explore Page & Search**  
***[NEW] *** *frontend/src/features/explore/ExplorePage.tsx*  
- Create an Explore page component.  
- The top section will have a search input. When typing, it will debounce and display a list of user search results (avatars + names) that link to their profiles.  
- The bottom section will render <PostFeed> using the new useGlobalFeed hook, allowing you to see posts from everyone on the platform.  
***[MODIFY] *** *frontend/src/App.tsx*  
- Add <Route path="explore" element={<ExplorePage />} /> under the AppShell routes.  
***[MODIFY] *** *frontend/src/components/AppShell.tsx*  
- Add a new RailButton with a Search or Compass icon linking to /explore.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OQQ2AQBAAsSE5CbzRujLwhwQMYIEfIWkVdJuZozoDAOAvrlWtav96AgDAa/cDEXQEKquakOYAAAAASUVORK5CYII=)  
**4. Frontend: Multi-line Message Input**  
***[MODIFY] *** *frontend/package.json*  
- Install react-textarea-autosize for premium, dynamic textarea expansion.  
***[MODIFY] *** *frontend/src/features/chat/MessageInput.tsx*  
- Replace the <input> element with <TextareaAutosize>.  
- Add an onKeyDown handler:  
  - If Enter is pressed without Shift (or Ctrl), submit the form.  
  - If Shift + Enter (or Ctrl + Enter) is pressed, allow the default behavior (inserting a new line).  
**Verification Plan**  
**Automated Tests**  
- Run npm run typecheck to ensure no TypeScript regressions.  
**Manual Verification**  
- Navigate to the Explore page and search for an existing user.  
- Verify the Global feed displays posts from users you don't follow.  
- Visit a user's profile from the search results and click "Follow".  
- Navigate to a chat and test sending a multi-line message using Shift+Enter.  
