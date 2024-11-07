import sys

import pymysql
from datetime import datetime

from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import create_connection, person_get_total, rsvp_get_with_comments, person_create, person_delete, person_list_with_rsvp_status, rsvp_get_total, init_db, person_get, rsvp_list_with_comments, person_update, rsvp_list, rsvp_toogle_status, comment_create, rsvp_confirm


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Manage Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# init database
init_db()

@app.get("/", response_class=HTMLResponse)
async def home_index(request: Request):
    rsvps = rsvp_list_with_comments()
    return templates.TemplateResponse("index.html", {"request": request, "person": None, "rsvps": rsvps})


## admin page persons
@app.get("/adm", response_class=HTMLResponse)
async def person_list(request: Request, search: str = None):
    persons = person_list_with_rsvp_status(search)

    total_persons = len(persons)
    total_male = len([p for p in persons if p['gender'] == 'male'])
    total_female = len([p for p in persons if p['gender'] == 'female'])
    total_rsvps = rsvp_get_total(show_all=True)

    return templates.TemplateResponse("adm/person_list.html", {
        "request": request,
        "persons": persons,
        "total_persons": total_persons,
        "total_male": total_male,
        "total_female": total_female,
        "total_rsvps": total_rsvps,
        "search": search,
    })

@app.get("/adm/person-add", response_class=HTMLResponse)
async def person_add_form(request: Request):
    return templates.TemplateResponse("adm/person_add.html", {
        "request": request,
        "error_message": None,
    })

@app.post("/adm/person-add", response_class=HTMLResponse)
async def person_add(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    gender: str = Form(...),
    title: str = Form(None),
):
    try:
        person_create(code, name.upper(), gender, title)
        return templates.TemplateResponse("adm/person_added.html", {"request": request, "name": name.upper()})
    except pymysql.IntegrityError as e:
        print(e)
        error_message = "Code already exists"
        return templates.TemplateResponse("adm/person_add.html", {
            "request": request,
            "error_message": error_message
        })
    except Exception as ee:
        print(ee)
        error_message = "An unexpected error occurred."
        return templates.TemplateResponse("adm/person_add.html", {
            "request": request,
            "error_message": error_message
        })

@app.get("/adm/person-edit/{code}", response_class=HTMLResponse)
async def person_edit_form(request: Request, code: str):
    person = person_get(code)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return templates.TemplateResponse("adm/person_edit.html", {
        "request": request,
        "person": person,
        "error_message": None
    })

@app.post("/adm/person-edit/{code}", response_class=HTMLResponse)
async def person_edit(
    request: Request,
    code: str,
    name: str = Form(...),
    gender: str = Form(...),
    title: str = Form(None),
):
    try:
        person_update(code, name.upper(), gender, title)
        return RedirectResponse(url="/adm", status_code=302)
    except pymysql.IntegrityError as e:
        print(e)
        error_message = "Code already exists"
        person = person_get(code)
        return templates.TemplateResponse("adm/person_edit.html", {
            "request": request,
            "person": person,
            "error_message": error_message
        })
    except Exception as ee:
        print(ee)
        error_message = "An unexpected error occurred."
        person = person_get(code)
        return templates.TemplateResponse("adm/person_edit.html", {
            "request": request,
            "person": person,
            "error_message": error_message
        })

@app.get("/adm/person-delete/{code}", response_class=HTMLResponse)
async def person_delete_form(request: Request, code: str):
    person = person_get(code)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return templates.TemplateResponse("adm/person_delete.html", {
        "request": request,
        "person": person
    })

@app.post("/adm/person-delete/{code}", response_class=HTMLResponse)
async def person_delete_action(request: Request, code: str):
    try:
        person_delete(code)
        return RedirectResponse(url="/adm", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Person delete error: {e}")

@app.get("/adm/rsvp", response_class=HTMLResponse)
async def rsvp_list_index(request: Request, attendance: str = None, has_last_comment: str = None):
    rsvps = rsvp_list(attendance, has_last_comment)

    total_rsvps = rsvp_get_total(show_all=True)
    total_no_hadir = len([rsvp for rsvp in rsvp_list(attendance='Tidak Hadir') if rsvp.get('is_active')])
    total_inactive = len([rsvp for rsvp in rsvp_list() if not rsvp.get('is_active')])
    total_hadir = total_rsvps - total_no_hadir - total_inactive

    return templates.TemplateResponse("adm/rsvp_list.html", {
        "request": request,
        "rsvps": rsvps,
        "selected_attendance": attendance,
        "selected_has_last_comment": has_last_comment,
        "total_rsvps": total_rsvps,
        "total_hadir": total_hadir,
        "total_no_hadir": total_no_hadir,
        "total_inactive": total_inactive
    })

@app.get("/adm/rsvp-detail/{rsvp_id}", response_class=HTMLResponse)
async def rsvp_detail(request: Request, rsvp_id: int):
    rsvp_with_comments = rsvp_get_with_comments(rsvp_id)
    if not rsvp_with_comments:
        raise HTTPException(status_code=404, detail="RSVP not found")
    return templates.TemplateResponse("adm/rsvp_detail.html", {
        "request": request, 
        "rsvp": rsvp_with_comments, 
        "comments": rsvp_with_comments['comments']
    })

@app.post("/adm/rsvp-toogle-status/{rsvp_id}")
async def rsvp_toogle_status_route(
    request: Request,
    rsvp_id: int,
):
    success = rsvp_toogle_status(rsvp_id)
    if success:
        rsvp = rsvp_get_with_comments(rsvp_id)
        return templates.TemplateResponse(
            "adm/rsvp_partial_status_section.html",
            {
                "request": request,
                "rsvp": rsvp
            }
        )
    else:
        raise HTTPException(status_code=404, detail="RSVP not found")

@app.post("/rsvp-confirm", response_class=HTMLResponse)
async def submit_form(
    request: Request, 
    name: str = Form(...), 
    message: str = Form(...), 
    attendance: str = Form(...)
):
    rsvp_id = rsvp_confirm(name.upper(), message, attendance)

    total_rsvps = rsvp_get_total()
    total_no_hadir = len([rsvp for rsvp in rsvp_list(attendance='Tidak Hadir') if rsvp.get('is_active')])
    total_persons = person_get_total()

    # Send Telegram notification
    notification_message = f"""✨New RSVP Submitted✨
------
*Name:* {name}
*Attendance:* {attendance}
*Message:* {message}

_Total RSVP:_ {total_rsvps}
_Total Hadir:_ *{total_rsvps - total_no_hadir}*
_Total Tidak Hadir:_ `{total_no_hadir}`
_Total Undangan:_ {total_persons}"""
    # TODO: Send notification to Telegram
    # await send_telegram_notification(notification_message)

    return templates.TemplateResponse(
        "adm/rsvp_confirm_response.html", 
        {
            "request": request, 
            "id": rsvp_id,
            "name": name, 
            "message": message, 
            "attendance": attendance,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@app.post("/adm/comment-add/{rsvp_id}", response_class=HTMLResponse)
async def submit_comment(
    request: Request,
    rsvp_id: int,
    name: str = Form(...),
    comment: str = Form(...)
):
    comment_create(rsvp_id, name, comment)
    return RedirectResponse(url=f"/adm/rsvp-detail/{rsvp_id}", status_code=302)


# always put this route to bottom to not conflict with other priority routes
@app.get("/{pid}", response_class=HTMLResponse)
async def home(request: Request, pid: str = None):
    person = person_get(pid) if pid else None
    rsvps = rsvp_list_with_comments()
    return templates.TemplateResponse("index.html", {"request": request, "person": person, "rsvps": rsvps})
