import * as React from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"

import { cn } from "../../lib/utils"
import { buttonVariants } from "@/components/ui/button"
import { format } from "date-fns"

function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  onSelect,
  selected,
  ...props
}) {
  const [currentMonth, setCurrentMonth] = React.useState(
    selected || new Date()
  );

  const daysInMonth = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth() + 1,
    0
  ).getDate();

  const firstDay = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth(),
    1
  ).getDay();

  const handlePrev = () => {
    setCurrentMonth(
      new Date(
        currentMonth.getFullYear(),
        currentMonth.getMonth() - 1,
        1
      )
    );
  };

  const handleNext = () => {
    setCurrentMonth(
      new Date(
        currentMonth.getFullYear(),
        currentMonth.getMonth() + 1,
        1
      )
    );
  };

  const handleSelectDay = (day) => {
    const date = new Date(
      currentMonth.getFullYear(),
      currentMonth.getMonth(),
      day
    );
    onSelect?.(date);
  };

  return (
    <div className={cn("p-3", className)}>
      {/* Header */}
      <div className="flex justify-center pt-1 relative items-center">
        <button
          className={cn(
            buttonVariants({ variant: "outline" }),
            "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100 absolute left-1"
          )}
          onClick={handlePrev}
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        <span className="text-sm font-medium">
          {format(currentMonth, "MMMM yyyy")}
        </span>

        <button
          className={cn(
            buttonVariants({ variant: "outline" }),
            "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100 absolute right-1"
          )}
          onClick={handleNext}
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      {/* Week Days */}
      <div className="w-full border-collapse space-y-1 mt-4">
        <div className="flex">
          {["S", "M", "T", "W", "T", "F", "S"].map((d) => (
            <div
              key={d}
              className="text-muted-foreground rounded-md w-8 font-normal text-[0.8rem] text-center"
            >
              {d}
            </div>
          ))}
        </div>

        {/* Days Grid */}
        <div className="flex flex-col w-full mt-2">
          <div className="flex flex-wrap w-full">
            {/* Empty spaces before 1st day */}
            {[...Array(firstDay)].map((_, i) => (
              <div key={`empty-${i}`} className="w-8 h-8" />
            ))}

            {/* Calendar Days */}
            {[...Array(daysInMonth)].map((_, i) => {
              const day = i + 1;
              const dateObj = new Date(
                currentMonth.getFullYear(),
                currentMonth.getMonth(),
                day
              );
              const isSelected =
                selected &&
                dateObj.toDateString() === selected.toDateString();

              return (
                <button
                  key={day}
                  onClick={() => handleSelectDay(day)}
                  className={cn(
                    buttonVariants({ variant: "ghost" }),
                    "h-8 w-8 p-0 font-normal text-center rounded-md",
                    isSelected &&
                      "bg-primary text-primary-foreground"
                  )}
                >
                  {day}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

Calendar.displayName = "Calendar";

export { Calendar };
