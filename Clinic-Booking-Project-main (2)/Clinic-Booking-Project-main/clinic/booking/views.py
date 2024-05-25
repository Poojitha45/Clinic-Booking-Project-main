from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, timedelta
from .models import Appointment
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def index(request):
    return render(request, "index.html", {})

def booking(request):
    # Calling 'validWeekday' function to loop days you want in the next 21 days:
    weekdays = validWeekday(22)

    # Only show the days that are not full:
    validateWeekdays = isWeekdayValid(weekdays)

    if request.method == 'POST':
        service = request.POST.get('service')
        day = request.POST.get('day')
        if not service:
            messages.success(request, "Please Select A Service!")
            return redirect('booking')

        # Store day and service in Django session:
        request.session['day'] = day
        request.session['service'] = service

        return redirect('bookingSubmit')

    return render(request, 'booking.html', {
        'weekdays': weekdays,
        'validateWeekdays': validateWeekdays,
    })

@login_required
def bookingSubmit(request):
    user = request.user
    times = [
        "3 PM", "3:30 PM", "4 PM", "4:30 PM", "5 PM", "5:30 PM", "6 PM", "6:30 PM", "7 PM", "7:30 PM"
    ]
    today = datetime.now()
    minDate = today.strftime('%Y-%m-%d')
    maxDate = (today + timedelta(days=21)).strftime('%Y-%m-%d')

    # Get stored data from Django session:
    day = request.session.get('day')
    service = request.session.get('service')

    # Only show the time of the day that has not been selected before:
    hour = checkTime(times, day)
    if request.method == 'POST':
        time = request.POST.get("time")
        date = dayToWeekday(day)

        if service:
            if minDate <= day <= maxDate:
                if date in ['Monday', 'Saturday', 'Wednesday']:
                    if Appointment.objects.filter(day=day).count() < 11:
                        if Appointment.objects.filter(day=day, time=time).count() < 1:
                            Appointment.objects.create(
                                user=user,
                                service=service,
                                day=day,
                                time=time,
                            )
                            messages.success(request, "Appointment Saved!")
                            return redirect('index')
                        else:
                            messages.success(request, "The Selected Time Has Been Reserved Before!")
                    else:
                        messages.success(request, "The Selected Day Is Full!")
                else:
                    messages.success(request, "The Selected Date Is Incorrect")
            else:
                messages.success(request, "The Selected Date Isn't In The Correct Time Period!")
        else:
            messages.success(request, "Please Select A Service!")

    return render(request, 'bookingSubmit.html', {
        'times': hour,
    })

@login_required
def delete_appointment(request, id):
    appointment = get_object_or_404(Appointment, pk=id)
    if appointment.user == request.user or request.user.is_staff:
        if request.method == 'POST':
            appointment.delete()
            messages.success(request, "Appointment deleted successfully!")
            return redirect('userPanel')
        
        return render(request, 'delete_confirm.html', {'appointment': appointment})
    else:
        messages.error(request, "You do not have permission to delete this appointment.")
        return redirect('userPanel')

@login_required
def userPanel(request):
    user = request.user
    appointments = Appointment.objects.filter(user=user).order_by('day', 'time')
    return render(request, 'userPanel.html', {
        'user': user,
        'appointments': appointments,
    })

@login_required
def userUpdate(request, id):
    appointment = get_object_or_404(Appointment, pk=id)
    userdatepicked = appointment.day
    today = datetime.today()
    minDate = today.strftime('%Y-%m-%d')
    delta24 = (userdatepicked >= today + timedelta(days=1))

    # Calling 'validWeekday' function to loop days you want in the next 21 days:
    weekdays = validWeekday(22)

    # Only show the days that are not full:
    validateWeekdays = isWeekdayValid(weekdays)

    if request.method == 'POST':
        service = request.POST.get('service')
        day = request.POST.get('day')

        # Store day and service in Django session:
        request.session['day'] = day
        request.session['service'] = service

        return redirect('userUpdateSubmit', id=id)

    return render(request, 'userUpdate.html', {
        'weekdays': weekdays,
        'validateWeekdays': validateWeekdays,
        'delta24': delta24,
        'id': id,
    })

@login_required
def userUpdateSubmit(request, id):
    user = request.user
    times = [
        "3 PM", "3:30 PM", "4 PM", "4:30 PM", "5 PM", "5:30 PM", "6 PM", "6:30 PM", "7 PM", "7:30 PM"
    ]
    today = datetime.now()
    minDate = today.strftime('%Y-%m-%d')
    maxDate = (today + timedelta(days=21)).strftime('%Y-%m-%d')

    day = request.session.get('day')
    service = request.session.get('service')

    # Only show the time of the day that has not been selected before and the time he is editing:
    hour = checkEditTime(times, day, id)
    appointment = get_object_or_404(Appointment, pk=id)
    userSelectedTime = appointment.time
    if request.method == 'POST':
        time = request.POST.get("time")
        date = dayToWeekday(day)

        if service:
            if minDate <= day <= maxDate:
                if date in ['Monday', 'Saturday', 'Wednesday']:
                    if Appointment.objects.filter(day=day).count() < 11:
                        if Appointment.objects.filter(day=day, time=time).count() < 1 or userSelectedTime == time:
                            appointment.user = user
                            appointment.service = service
                            appointment.day = day
                            appointment.time = time
                            appointment.save()
                            messages.success(request, "Appointment Edited!")
                            return redirect('index')
                        else:
                            messages.success(request, "The Selected Time Has Been Reserved Before!")
                    else:
                        messages.success(request, "The Selected Day Is Full!")
                else:
                    messages.success(request, "The Selected Date Is Incorrect")
            else:
                messages.success(request, "The Selected Date Isn't In The Correct Time Period!")
        else:
            messages.success(request, "Please Select A Service!")
        return redirect('userPanel')

    return render(request, 'userUpdateSubmit.html', {
        'times': hour,
        'id': id,
    })

@login_required
def staffPanel(request):
    today = datetime.today()
    minDate = today.strftime('%Y-%m-%d')
    maxDate = (today + timedelta(days=21)).strftime('%Y-%m-%d')
    
    # Only show the Appointments 21 days from today
    items = Appointment.objects.filter(day__range=[minDate, maxDate]).order_by('day', 'time')

    return render(request, 'staffPanel.html', {
        'items': items,
    })

def dayToWeekday(x):
    z = datetime.strptime(x, "%Y-%m-%d")
    y = z.strftime('%A')
    return y

def validWeekday(days):
    # Loop days you want in the next 21 days:
    today = datetime.now()
    weekdays = []
    for i in range(days):
        x = today + timedelta(days=i)
        y = x.strftime('%A')
        if y in ['Monday', 'Saturday', 'Wednesday']:
            weekdays.append(x.strftime('%Y-%m-%d'))
    return weekdays
    
def isWeekdayValid(x):
    validateWeekdays = []
    for j in x:
        if Appointment.objects.filter(day=j).count() < 10:
            validateWeekdays.append(j)
    return validateWeekdays

def checkTime(times, day):
    # Only show the time of the day that has not been selected before:
    x = [k for k in times if Appointment.objects.filter(day=day, time=k).count() < 1]
    return x

def checkEditTime(times, day, id):
    # Only show the time of the day that has not been selected before:
    appointment = get_object_or_404(Appointment, pk=id)
    time = appointment.time
    x = [k for k in times if Appointment.objects.filter(day=day, time=k).count() < 1 or time == k]
    return x
