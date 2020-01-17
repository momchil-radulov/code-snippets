using System.Linq;

private readonly ApplicationDbContext _dbContext;

public class AccountController : Controller (ApplicationDbContext dbContext)
{
  _dbContext = dbContext;
}

async public Task<IActionResult> Notifications()
{
    List<NotificationLog> notifications;
    var user = await _userManager.GetUserAsync(User);
    var userId = user.Id;
    notifications = (from l in _dbContext.NotificationLogs
                     join u in _dbContext.ApplicationUsers on l.User equals u
                     join d in _dbContext.Devices on l.DeviceId equals d.Id
                     where u.Id == userId
                     orderby l.Time descending
                     select new ProjectName.Data.Models.NotificationLog
                     { Id = l.Id, Time = l.Time, Title = l.Title, Data = l.Data, User = u, Device = d })
                     .ToList();
    return View(notifications);
}

In view file Notifications.cshtml:

@model IEnumerable<ProjectName.Data.Models.NotificationLog>
@using Microsoft.AspNetCore.Mvc.Localization
@inject IViewLocalizer Localizer

@{
    ViewData["Title"] = "Notifications";
    Layout = "~/Views/Shared/_Layout.cshtml";
    var serialNo = ViewBag.serialNo;
}

<h2>@Localizer["Notifications"]</h2>

<table class="table">
    <thead>
        <tr>
            <th>
                @Html.DisplayNameFor(model => model.Device.Name)
            </th>
            <th>
                @Localizer["Title"]
            </th>
        </tr>
    </thead>
    <tbody>
        @foreach (var item in Model)
        {
        <tr>
            <td>
                <a asp-controller="Devices" asp-action="Status" asp-route-id="@item.Device.Id">@Html.DisplayFor(modelItem => item.Device.Name)</a>
            </td>
            <td>
                @Html.DisplayFor(modelItem => item.Title)
            </td>
        </tr>
        }
    </tbody>
</table>
